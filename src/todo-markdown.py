import fileinput
import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import os
import re
import textwrap


class quicknote_markdown(kp.Plugin):
    """
    Manages Notess in a Markdown file

    Plugin that gives you the ability to 
    add/finish/delete Notess that are stored in a markdown file
    """

    QUICKNOTE_CAT = kp.ItemCategory.USER_BASE + 10
    ADD_QUICKNOTE_CAT = kp.ItemCategory.USER_BASE + 20

    FINISH_QUICKNOTE_NAME = "finish"
    FINISH_QUICKNOTE_LABEL = "Finish the Todo"

    DELETE_QUICKNOTE_NAME = "delete"
    DELETE_QUICKNOTE_LABEL = "Delete the Todo"

    _quicknotes = []

    def __init__(self):
        super().__init__()

    def _read_config(self):
        settings = self.load_settings()

        # It's the folder FOLDERID_Documents ("%USERPROFILE%\Documents")
        # https://docs.microsoft.com/sv-se/windows/win32/shell/knownfolderid?redirectedfrom=MSDN
        
        default_path = kpu.shell_known_folder_path(
            "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
        )
        self._filepath = settings.get_stripped(
            "file_path", "main", default_path
        )

        if os.path.isdir(self._filepath):
            self._filepath = os.path.join(self._filepath, "QuickNote.md")

    def on_start(self):
        self._debug = False
        self._read_config()

        self.set_actions(self.QUICKNOTE_CAT, [
            self.create_action(
                name=self.FINISH_QUICKNOTE_NAME,
                label=self.FINISH_QUICKNOTE_LABEL,
                short_desc="Finish the Note"
            ),
            self.create_action(
                name=self.DELETE_QUICKNOTE_NAME,
                label=self.DELETE_QUICKNOTE_LABEL,
                short_desc="Removes the Note completely"
            ),
        ])

    def on_catalog(self):
        catalog = []

        catalog.append(self.create_item(
            category=kp.ItemCategory.KEYWORD,
            label="QuickNote",
            short_desc="Manages Notes",
            target="quicknote",
            args_hint=kp.ItemArgsHint.REQUIRED,
            hit_hint=kp.ItemHitHint.KEEPALL
        ))

        self.set_catalog(catalog)

    def on_suggest(self, user_input, items_chain):

        if not items_chain:
            return

        suggestions = self._quicknotes[:]

        if user_input:
            target = user_input.strip().format(q=user_input.strip())
            suggestions.append(
                self.create_item(
                    category=self.ADD_QUICKNOTE_CAT,
                    label="Add as Note: '{}'".format(user_input),
                    short_desc=target,
                    target=target,
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE,
                    loop_on_suggest=False
                )
            )

        self.set_suggestions(suggestions, kp.Match.DEFAULT, kp.Sort.NONE)

    def on_execute(self, item, action):
        if item.category() == self.ADD_QUICKNOTE_CAT:
            self._add_quicknote(item.short_desc())

        if item and item.category() == self.QUICKNOTE_CAT:
            if action and action.name() == self.FINISH_QUICKNOTE_NAME:
                self._finish_quicknote(item.label())
            if action and action.name() == self.DELETE_QUICKNOTE_NAME:
                self._delete_quicknote(item.label())

    def on_activated(self):
        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                markdown = f.read()

                self._quicknotes = []
                quicknotes = self._fetch_all_open_quicknotes(markdown)

                for quicknote in quicknotes:
                    self._quicknotes.append(self._create_suggestion(
                        quicknote.split("]")[1]
                    ))
        except FileNotFoundError as e:
            self.warn(e)

    def on_events(self, flags):
        if flags & kp.Events.PACKCONFIG:
            self._read_config()

    def _fetch_all_open_quicknotes(self, markdown):
        regex = r'\[[[ ]*\].+'
        return re.findall(regex, markdown)

    def _finish_quicknote(self, quicknote):
        try:
            with open(self._filepath, 'r', encoding="utf-8") as f:
                newlines = []
                for line in f.readlines():
                    if quicknote in line:
                        newlines.append(line.replace("-", " -", 1))
                    else:
                        newlines.append(line)

            with open(self._filepath, 'w', encoding="utf-8") as f:
                for line in newlines:
                    f.write(line)
        except Exception as e:
            self.err(e)

    def _add_quicknote(self, quicknote):
        try:
            with open(self._filepath, 'a+', encoding="utf-8") as f:
                f.write("\n---\n- {}".format(quicknote))
        except Exception as e:
            self.err(e)

    def _delete_quicknote(self, quicknote):
        try:
            with open(self._filepath, 'r', encoding="utf-8") as f:
                newlines = []
                for line in f.readlines():
                    if quicknote not in line:
                        newlines.append(line)
            with open(self._filepath, 'w', encoding="utf-8") as f:
                for line in newlines:
                    f.write(line)
        except Exception as e:
            self.err(e)

    def _create_suggestion(self, item):

        text = textwrap.wrap(item, width=50)
        label = text.pop(0)

        return self.create_item(
            category=self.QUICKNOTE_CAT,
            label=label,
            short_desc="".join(text),
            target=item.strip().format(q=item.strip()),
            args_hint=kp.ItemArgsHint.FORBIDDEN,
            hit_hint=kp.ItemHitHint.IGNORE,
        )
