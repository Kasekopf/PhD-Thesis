import bibtexparser
import glob


class BibFile:
    def __init__(self, filename, content_dir):
        self.__filename = filename
        self.__content_dir = content_dir

        with open(self.__filename) as bib_file:
            self.__entries = bibtexparser.load(bib_file).entries

        self.__replacements = {}

    def save(self):
        self.save_bib()
        self.save_content()

    def save_bib(self):
        db = bibtexparser.bibdatabase.BibDatabase()
        db.entries = self.__entries

        writer = bibtexparser.bwriter.BibTexWriter()
        writer.order_entries_by = None
        writer.indent = "  "
        # Match default Google scholar order
        writer.display_order = [
            "title",
            "author",
            "journal",
            "booktitle",
            "volume",
            "number",
            "pages",
            "year",
            "publisher",
        ]
        with open(self.__filename, "w") as bib_file:
            output = writer.write(db)
            output = output.replace(" = ", "=")  # Match Google scholar style
            bib_file.write(output)

    def save_content(self):
        # Perform the requested replacements
        for filename in glob.iglob(self.__content_dir + "**/**/*.tex", recursive=True):
            with open(filename) as file:
                data = file.read()
            for old_id, new_id in self.__replacements.items():
                data = data.replace(old_id, new_id)
            with open(filename, "w") as file:
                file.write(data)

    def replace(self, old_id, new_id):
        print("   " + old_id + " => " + new_id)
        self.__replacements[old_id] = new_id

    def booktitles(self):
        return {e["booktitle"] for e in self.__entries if "booktitle" in e}

    def journals(self):
        return {e["journal"] for e in self.__entries if "journal" in e}

    def dedup_titles(self):
        """
        Remove all entries with duplicate titles, keeping only the first instance.
        """

        def canonicalize(raw_title):
            return "".join(c.lower() for c in raw_title if c.isalnum())

        titles = {}
        new_db = []
        for entry in self.__entries:
            title = canonicalize(entry["title"])
            if title in titles:
                print(title)
                self.replace(entry["ID"], titles[title])
            else:
                titles[title] = entry["ID"]
                new_db.append(entry)
        self.__entries = new_db


def do():
    bib = BibFile("../main.bib", "../content")
    bib.dedup_titles()
    bib.save()

    for e in bib.booktitles():
        print(e)


do()
