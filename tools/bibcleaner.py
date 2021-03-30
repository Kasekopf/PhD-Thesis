import bibtexparser


class BibFile:
    def __init__(self, filename, content_dir):
        self.__filename = filename
        self.__content_dir = content_dir

        with open("../main.bib") as bib_file:
            self.__entries = bibtexparser.load(bib_file).entries
        self.__replacements = {}

    def save(self):
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
        with open("../main.bib", "w") as bib_file:
            output = writer.write(db)
            output = output.replace(" = ", "=")  # Match Google scholar style
            bib_file.write(output)

    def replace(self, old_id, new_id):
        print("   " + old_id + " => " + new_id)
        self.__replacements[old_id] = new_id

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
    bib.save()


do()
