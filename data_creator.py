import random
import sqlite3
# import tempfile
import os
import sys
import csv
import json
import re
import calendar
import string

class DataCreator:
    calculated_types = (
        "age",
        "money",
        "gender",
        "race",
        "languages",
        "continents"
    )
    credit_card_regex = (
        ("Visa", "Visa", "^4[0-9]{12}(?:[0-9]{3})?$"),
        ("MasterCard", "MC", "^(?:5[1-5][0-9]{2}|222[1-9]|22[3-9][0-9]|2[3-6][0-9]{2}|27[01][0-9]|2720)[0-9]{12}$"),
        ("American Express", "AMEX", "^3[47][0-9]{13}$"),
        ("Diners Club", "DC", "^3(?:0[0-5]|[68][0-9])[0-9]{11}$"),
        ("Discover", "DISC", "^6(?:011|5[0-9]{2})[0-9]{12}$"),
        ("JCB", "JCB", "^(?:2131|1800|35\d{3})\d{11}$")
    )
    
    def __init__(self):
        self.root = os.path.dirname(os.path.abspath(__file__))

        self.lists = os.path.join(self.root, "lists")

        self.db_filename = os.path.join(self.root, "database.db")
        
        self.number_pattern = re.compile("^\d+$")
        self.variable_pattern = re.compile("%[a-zA-Z_]+(,[a-zA-Z1-9_=]+)*%")

        self.variable_substitutions = {
            "lastname": self.lastname,
            "firstname": self.firstname,
            #"company": self.company_name,
            "and": self.random_amp,
            "company_suffix": self.company_suffix,
            #"zip": self.zip,
            "state": self.state,
            "area_code": self.area_code,
            "nickname": self.nickname,
            "country": self.country,
            "company_noun": self.company_noun,
            "optional_comma": self.optional_comma,
            "random_letters": self.random_letters,
            "adjective": self.adjective
        }

        # if os.path.exists(self.db_filename):
        #     os.remove(self.db_filename)
        have_db = True

        if not os.path.exists(self.db_filename):
            have_db = False

        self.db = sqlite3.connect(self.db_filename)
        if not have_db:
            self._initialize()

    def adjective(self, optional=False, space=False):
        if optional:
            if not random.randint(0,1):
                return ""
        rowid = self.random_row("adjective")
        output = self.correct_case(self.get_scalar("SELECT adjective FROM adjective WHERE rowid = ?", (rowid,)))
        if space:
            output += " "
        return output

    def optional_comma(self):
        if random.randint(0, 1):
            return ","
        return ""

    def _initialize(self):
        self._init_name_last()
        self._init_name_first()
        self._init_country()
        self._init_city()
        self._init_state()
        self._init_zip()
        self._init_area_code()
        self._init_nickname()
        self._init_street_suffix()
        self._init_company_suffix()
        self._init_company_noun()
        self._init_adjective()
        self._init_credit_card()
        # self._init_company_word()
    
    def _init_credit_card(self):
        print("Initializing credit cards...")
        sql = """
        CREATE TABLE credit_card (
            name text NOT NULL,
            longname text,
            number text NOT NULL PRIMARY KEY
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_creditcard_name ON credit_card(name)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "credit_card.csv")
        with open(input_file_name, "r") as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                name = row[0]
                longname = row[1]
                number = row[2]
                sql = "INSERT INTO credit_card (name, longname, number) VALUES (?, ?, ?)"
                values = (name, longname, number)
                self.exec_statement(sql, values)
            self.db.commit()

    def _init_city(self):
        print("Initializing cities...")
        sql = """
        CREATE TABLE city (
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            state TEXT
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_city_name ON city(name)")
        self.exec_statement("CREATE INDEX idx_city_country ON city(country)")
        self.exec_statement("CREATE INDEX idx_city_state ON city(state)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "city.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline() # Skip header
            reader = csv.reader(f_in)
            for row in reader:
                name = row[0]
                country = row[1]
                state = row[2]
                sql = "INSERT INTO city (name, country, state) VALUES (?, ?, ?)"
                values = [name, country, state]
                self.exec_statement(sql, values)
            self.db.commit()


    def _init_street_suffix(self):
        print("Initializing street suffixes...")
        sql = """
        CREATE TABLE street_suffix (
            suffix text
        )
        """
        self.exec_statement(sql)
        sql = """
        CREATE TABLE street_suffix_abbr (
            abbr text,
            suffix_id number
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_streetsuffix ON street_suffix(suffix)")
        self.exec_statement("CREATE INDEX idx_streetsuffix_abbr ON street_suffix_abbr(abbr)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "street_suffix.csv")
        with open(input_file_name, "r") as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                root = row[0]
                abbrs = sorted(list(set(row[1:])))

                sql = """INSERT INTO street_suffix (suffix) VALUES (?)"""
                values = (root,)
                self.exec_statement(sql, values)

                for abbr in abbrs:
                    if abbr == root:
                        continue
                    sql = """SELECT rowid FROM street_suffix WHERE suffix = ?"""
                    values = (root,)
                    rowid = self.get_scalar(sql, values)
                    sql = """INSERT INTO street_suffix_abbr (abbr, suffix_id) VALUES (?, ?)"""
                    values = (abbr, rowid)
                    self.exec_statement(sql, values)
            self.db.commit()

    def _init_area_code(self):
        print("Initializing area codes...")
        sql = """
        CREATE TABLE area_code (
            code integer,
            city text,
            state text,
            country_code text
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_areacode_code ON area_code(code)")
        self.exec_statement("CREATE INDEX idx_areacode_city ON area_code(city)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "area_code.csv")
        with open(input_file_name) as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                sql = """
                INSERT INTO area_code (
                    code,
                    city,
                    state,
                    country_code
                )
                VALUES (?, ?, ?, ?)
                """
                values = [row[0], row[1], row[2], row[3]]
                self.exec_statement(sql, values)
            self.db.commit()
    
    def list_to_lower(self, _list):
        return [_.lower() for _ in _list]

    def _init_zip(self):
        print("Initializing zips...")
        sql = """
        CREATE TABLE zip (
            zip text NOT NULL,
            city text,
            state_abbr text,
            county text,
            citytype text,
            timezone integer,
            dst integer,
            classificationcode text
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_zip_zip ON zip(zip)")
        self.exec_statement("CREATE INDEX idx_zip_city ON zip(city)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "zip.csv")
        with open(input_file_name) as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
                row = self.list_to_lower(row)
                sql = """
                INSERT INTO zip (
                    zip,
                    city,
                    state_abbr,
                    county,
                    citytype,
                    timezone,
                    dst,
                    classificationcode
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.exec_statement(sql, row)
            self.db.commit()
    
    def _init_state(self):
        print("Initializing states...")
        sql = """
        CREATE TABLE state (
            name text PRIMARY KEY,
            abbreviation text,
            capital text,
            status integer
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_state_nam ON state(name)")
        self.exec_statement("CREATE INDEX idx_state_abbr ON state(abbreviation)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "state.csv")

        with open(input_file_name) as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
                sql = """
                INSERT INTO state (
                    abbreviation,
                    name,
                    capital,
                    status
                )
                VALUES (?, ?, ?, ?)
                """
                self.exec_statement(sql, row)
            self.db.commit()


    def _init_country(self):
        print("Initializing countries...")
        sql = """
        CREATE TABLE country (
            abbr_twoletter text,
            abbr_currency text,
            currency_name text,
            name_formal text,
            name_short text,
            name_fallback text,
            capital text,
            continent text
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_country_twoletter ON country(abbr_twoletter)")
        self.exec_statement("CREATE INDEX idx_country_nameformal ON country(name_formal)")
        self.exec_statement("CREATE INDEX idx_country_nameshort ON country(name_short)")
        self.exec_statement("CREATE INDEX idx_country_fallback ON country(name_fallback)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "country.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
                row = self.clean_empty(row)
                sql = """
                INSERT INTO country (
                    abbr_twoletter,
                    abbr_currency,
                    currency_name,
                    name_formal,
                    name_short,
                    name_fallback,
                    capital,
                    continent
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.exec_statement(sql, row)
            self.db.commit()

    def _init_name_first(self):
        print("Initializing first names...")
        sql = """
        CREATE TABLE first_name (
            year int NOT NULL,
            first_name text NOT NULL,
            percent real NOT NULL,
            sex text NOT NULL
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_firstname_firstname ON first_name(first_name)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "name_first.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
                row = self.clean_empty(row)
                sql = """
                INSERT INTO first_name (
                    year,
                    first_name,
                    percent,
                    sex
                )
                VALUES (?, ?, ?, ?)
                """
                self.exec_statement(sql, row)
            self.db.commit()

    def _init_nickname(self):
        print("Initializing nicknames...")    
        sql = """
        CREATE TABLE nickname (
            nickname text NOT NULL PRIMARY KEY
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_nickname_nickname ON nickname(nickname)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "nickname.txt")
        with open(input_file_name, "r") as f_in:
            for line in f_in:
                line = line.strip()
                sql = """
                INSERT INTO nickname (
                    nickname
                )
                VALUES
                (?)
                """
                values = (line,)
                self.exec_statement(sql, values)
            self.db.commit()

    # def _init_company_word(self):
    #     print("Initializing company words...")
    #     sql = """
    #     CREATE TABLE company_word (
    #         word text NOT NULL PRIMARY KEY UNIQUE
    #     )
    #     """
    #     self.exec_statement(sql)
    #     self.exec_statement("CREATE INDEX idx_companyword_word ON company_word(word)")
    #     self.db.commit()

    #     input_file_name = os.path.join(self.lists, "company_word.txt")
        
    #     manual_company_words = [
    #         "et al",
    #         "inc",
    #         "Inc",
    #         "llc",
    #         "LLC",
    #         "Co",
    #         "Esq",
    #         "mfg",
    #         "Corp"
    #     ]

    #     for word in manual_company_words:
    #         sql = """
    #         INSERT INTO company_word (
    #             word
    #         )
    #         VALUES (?)
    #         """
    #         values = (word,)
    #         self.exec_statement(sql, values)
    #     self.db.commit()

    #     with open(input_file_name, "r") as f_in:
    #         count = 0
    #         count2 = 0
    #         for line in f_in:
    #             line = line.strip()
    #             if self.is_name(line):
    #                 continue
    #             if self.is_word(line):
    #                 continue

    #             sql = """
    #             INSERT INTO company_word (
    #                 word
    #             )
    #             VALUES (?)
    #             """
    #             values = (line,)
    #             self.exec_statement(sql, values)
    #         self.db.commit()

    # def company_word(self):
    #     max_rowid = self.get_scalar("SELECT max(rowid) FROM company_word")
    #     rowid = random.randint(1, max_rowid)

    #     sql = "SELECT word FROM company_word WHERE rowid = ?"
    #     values = (rowid,)
    #     return self.get_scalar(sql, values)

    # def is_word(self, word):
    #     sql = "SELECT COUNT(*) FROM company_word WHERE word = ?"
    #     values = (word,)
    #     data = self.get_scalar(sql, values)
    #     return data > 0

    def is_name(self, word):
        sql = "SELECT COUNT(*) FROM last_name WHERE last_name = ?"
        values = (word,)
        data = self.get_scalar(sql, values)
        return data > 0
    
    def _init_company_suffix(self):
        print("Initializing company suffixes...")
        sql = """
        CREATE TABLE company_suffix (
            suffix text NOT NULL PRIMARY KEY
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_companysuffix_suffix on company_suffix(suffix)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "company_suffix.txt")
        with open(input_file_name, "r") as f_in:
            f_in.readline()
            for line in f_in:
                line = line.strip()
                sql = "INSERT INTO company_suffix (suffix) VALUES (?)"
                values = [line,]
                self.exec_statement(sql, values)
            self.db.commit()

    def _init_company_noun(self):
        print("Initializing job types...")
        sql = """
        CREATE TABLE company_noun (
            type text NOT NULL PRIMARY KEY UNIQUE
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_jobtype_type ON company_noun(type)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "company_noun.txt")
        with open(input_file_name, "r") as f_in:
            for line in f_in:
                line = line.strip()
                sql = "INSERT INTO company_noun (type) VALUES (?)"
                values = [line,]
                self.exec_statement(sql, values)
            self.db.commit()

    def _init_name_last(self):
        print("Initializing last names...")
        sql = """
        CREATE TABLE last_name (
            last_name text NOT NULL PRIMARY KEY,
            rank int,
            count int,
            pctwhite real,
            pctblack real,
            pctapi real,
            pctaian real,
            pct2prace real,
            pcthispanic real
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_lastname_lastname ON last_name(last_name)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "name_last.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
                row = self.clean_empty(row)
                sql = """
                INSERT INTO last_name (
                    last_name,
                    rank,
                    count,
                    pctwhite,
                    pctblack,
                    pctapi,
                    pctaian,
                    pct2prace,
                    pcthispanic
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                values = [row[0], row[1], row[2], row[5], row[6], row[7], row[8], row[9], row[10]]
                self.exec_statement(sql, values)
            self.db.commit()

    def _init_adjective(self):
        print("Initializing adjectives...")
        sql = """
        CREATE TABLE adjective (
            adjective text NOT NULL PRIMARY KEY
        )
        """
        self.exec_statement(sql)
        self.exec_statement("CREATE INDEX idx_adjective_adjective ON adjective(adjective)")
        self.db.commit()

        input_file_name = os.path.join(self.lists, "adjective.txt")
        with open(input_file_name, "r") as f_in:
            for line in f_in:
                line = line.strip()
                sql = "INSERT INTO adjective (adjective) VALUES (?)"
                values = (line,)
                self.exec_statement(sql, values)
            self.db.commit()

    def fix_capital_letters(self, statement):
        words = statement.split()
        output = " ".join(["{}{}".format(word[0].upper(), word[1:].lower()) for word in words])
        return output

    def clean_empty(self, row):
        out_row = []
        for item in row:
            if item.strip() == "":
                item = None
            out_row.append(item)
        return out_row

    def get_rows(self, sql, values=None):
        cur = self.db.cursor()
        if values:
            cur.execute(sql, values)
        else:
            cur.execute(sql)
        return cur.fetchall()

    def get_row(self, sql, values=None):
        results = self.get_rows(sql, values)
        if len(results) == 0:
            return results
        return results[0]

    def get_scalar(self, sql, values=None):
        results = self.get_row(sql, values)
        if len(results) == 0:
            return None
        return results[0]
    
    def exec_statement(self, sql, values=None):
        if values:
            self.get_rows(sql, values)
        else:
            self.get_rows(sql)
        return

    #def credit_card(self,name=None):
        

    def firstname(self, sex=None, boy=False, girl=False):
        if isinstance(sex, str):
            if sex.lower() in ("boy", "man", "male"):
                boy = True
            elif sex.lower() in ("girl", "woman", "female"):
                girl = True
        if boy == True and girl == True:
            raise ValueError("Boy and Girl cannot both be true")

        name = None

        while not name:
            rowid = self.random_row("first_name")
            sql = "SELECT first_name FROM first_name WHERE rowid = {}".format(rowid)

            if boy:
                sql += " AND sex = 'boy'"
            elif girl:
                sql += " AND sex = 'girl'"
            name = self.get_scalar(sql)
        return name
    
    def city(self, state=None):
        if not state:
            rowid = self.random_row("city")
            sql = "SELECT name FROM city WHERE rowid = ?"
            values = [rowid,]
            return self.correct_case(self.get_scalar(sql, values))
        else:
            sql = "SELECT * FROM city WHERE state = ?"
            values = [state,]
            data = self.get_rows(sql, values)
            rowid = random.randint(0, len(data) - 1)
            return data[rowid][0]


    def zip(self, state=None, city=None):
        if not city and not state:
            rowid = self.random_row("zip")
            sql = "SELECT zip FROM zip WHERE rowid = ?"
            values = [rowid,]
            if state:
                sql += " AND state_abbr = ?"
                values.append(state)
            if city:
                sql += " AND city = ?"
                values.append(city)
            return self.correct_case(self.get_scalar(sql, values))
        else:
            sql = "SELECT zip FROM zip WHERE "
            values = []
            if state:
                state = state.lower()
                sql += " state_abbr = ?"
                values.append(state)
            if state and city:
                sql += " AND "
            if city:
                city = city.lower()
                sql += " city = ?"
                values.append(city)
            data = self.get_rows(sql, values)
            rowid = random.randint(0, len(data) - 1)
            return data[rowid][0]

    def country(self):
        rowid = self.random_row("country")
        return self.correct_case(self.get_scalar("SELECT name_fallback FROM country WHERE rowid = ?", [rowid,]))

    def company_suffix(self, optional=False, space=False):
        if not random.randint(0, 1):
            return ""
        rowid = self.random_row("company_suffix")

        suffix = self.get_scalar("SELECT suffix FROM company_suffix WHERE rowid = {}".format(rowid))
        if space:
            suffix += " "
        return suffix

    def lastname(self):
        rowid = self.random_row("last_name")

        name = self.get_scalar("SELECT last_name FROM last_name WHERE rowid = {}".format(rowid))
        if random.randint(1, 20) == 1:
            rowid = self.random_row("last_name")
            name2 = self.get_scalar("SELECT last_name FROM last_name WHERE rowid = {}".format(rowid))
            name = "{}-{}".format(name, name2)
        return self.correct_case(name)
    
    def correct_case_word(self, word):
        return "{}{}".format(word[0].upper(), word[1:].lower())

    def correct_case(self, word):
        if word == None:
            return word
        words = word.split(" ")
        word = " ".join(self.correct_case_word(_) for _ in words)
        words = word.split("-")
        word = "-".join(self.correct_case_word(_) for _ in words)
        return word
    
    def age(self, no_distribution=False, category=None):
        if isinstance(category, str):
            category = category.lower()
        lower_bound = -1
        upper_bound = -1
        if not category:
            groups = ((0, 14), (15, 24), (25, 54), (55, 64), (65, 89), (91, 105))
            dist   = (1862, 3174, 7103, 8397, 9700, 10000)
            grouping = random.randint(0, 10000)
            group = -1
            for d in range(len(dist)):
                if grouping <= dist[d]:
                    return random.randint(groups[d][0], groups[d][1])
            raise NotImplementedError("You shouldn't be able to get this.")
        elif category == "any":
            lower_bound = 0
            upper_bound = 105
        elif category == "baby":
            lower_bound = 0
            upper_bound = 1
        elif category == "infant":
            lower_bound = 1
            upper_bound = 2
        elif category == "toddler":
            lower_bound = 2
            upper_bound = 3
        elif category == "child":
            lower_bound = 0
            upper_bound = 17
        elif category == "preteen":
            lower_bound = 10
            upper_bound = 12
        elif category == "teen":
            lower_bound = 13
            upper_bound = 19
        elif category == "young adult":
            lower_bound = 18
            upper_bound = 25
        elif category == "adult":
            lower_bound = 18
            upper_bound = 105
        elif "middle" in category:
            lower_bound = 35
            upper_bound = 55
        elif "retire" in category:
            lower_bound = 65
            upper_bound = 105
        else:
            raise NotImplementedError("The age category you have specified does not exist.")
        return random.randint(lower_bound, upper_bound)
    
    def company_noun(self):
        rowid = self.random_row("company_noun")
        return self.correct_case(self.get_scalar("SELECT type FROM company_noun WHERE rowid = ?", (rowid,)))

    def state(self, allow_territories=True, allow_military=True, allow_states=True, state=None):
        rowid = self.random_row("state")

        if state == None:
            sql = "SELECT abbreviation FROM state WHERE rowid = {} AND status in (".format(rowid)
            if allow_states:
                sql += "0, "
            if allow_military:
                sql += "1, "
            if allow_territories:
                sql += "2"
            sql += ")"

            return self.get_scalar(sql)
        else:
            sql = "SELECT "
    
    # def city(self, state=None):
    #     rowid = self.random_row("zip")

    #     sql = "SELECT city, state_abbr FROM zip WHERE rowid = {}".format(rowid)
    #     if state:
    #         sql += " AND state_abbr = '{}'".format(state)
    #     return ", ".join(self.get_row(sql))

    def area_code(self, country_code=None):
        rowid = self.random_row("area_code")

        sql = "SELECT code FROM area_code WHERE rowid = ?"
        values = [rowid,]
        if country_code:
            sql += "AND country_code = ?"
            values.append(country_code)
        return str(self.get_scalar(sql, values))

    def max_rowid(self, table):
        return self.get_scalar("SELECT MAX(rowid) FROM {}".format(table))

    def random_row(self, table):
        return random.randint(1, self.max_rowid(table))

    def nickname(self):
        rowid = self.random_row("nickname")

        return self.correct_case(self.get_scalar("SELECT nickname FROM nickname WHERE rowid = ?", [rowid,]))

    def number(self, start, end=None):
        if not end:
            end = start
            start = 1
        
        return random.randint(start, end)
    
    def money(self, start, end=None):
        if not end:
            end = start
            start = 0.00
        
        start *= 100
        end *= 100

        number = random.randint(start, end)
        return number / 100
    
    def letters(self, count=1, period=False, space=False):
        output = ""
        if count:
            count = int(count)
        for _ in range(count):
            output += random.choice(string.ascii_uppercase)
            if period:
                output += "."
            if space:
                output += " "
        return output

    def randand(self):
        odds = random.randint(0, 1)
        if odds:
            return "&"
        return "and"

    def randsons(self):
        sons = ("son", "sons", "Son", "Sons")
        odds = random.randint(0, len(sons) - 1)
        return sons[odds]

    def has_variable(self, statement):
        if self.variable_pattern.search(statement):
            return True
        return False

    def _handle_variables(self, statement):
        while self.has_variable(statement):
            for key, value in self.variable_substitutions.items():
                pattern_string = "%{}(,[a-zA-Z1-9=_]+)*%".format(key)
                pattern = re.compile(pattern_string)
                _data = pattern.search(statement)
                while _data:
                    _input = _data.group(0)[1:-1]
                    kw = {}
                    if "," in _input:
                        _variables = _input.split(",")[1:]
                        for _var in _variables:
                            if "=" in _var:
                                key2, value2 = _var.split("=")
                            else:
                                key2 = _var
                                value2 = True
                            kw[key2] = value2
                    
                    statement = re.sub(pattern_string, value(**kw), statement)
                    _data = pattern.search(statement)
        return statement

    def random_amp(self):
        _possibles = ("&", "and", "And")
        return random.choice(_possibles)

    def random_letters(self, count=1, period=False, space=False):
        output = ""
        count = int(count)
        for _ in range(count):
            output += random.choice(string.ascii_uppercase)
            if period:
                output += "."
            if space:
                output += " "
        return output
    #def generate_rows(self, pattern):


    def company_name(self):
        formats = (
            "%lastname%, %lastname%, %and% %lastname% %company_suffix,optional%",
            "%lastname% %and% %lastname% %company_suffix,optional%",
            "%adjective,optional,space%%nickname%'s %company_noun% %company_suffix,optional%",
            "%random_letters,count=3%"
        )
        rowid = random.randint(0, len(formats) - 1)
        return self._handle_variables(formats[rowid])
    

def main():
    d = DataCreator()
    print(d.company_name())
    statement = "%lastname%, %lastname%, %and% %lastname% %company_suffix,optional%"
    print(d._handle_variables(statement))

if __name__ == "__main__":
    main()
