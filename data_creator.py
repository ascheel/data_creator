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
    def __init__(self, **kwargs):
        """
        :keyword verbose:     boolean. adds extra verbosity to stdout
        :keyword new_file:    boolean. Forces new database file creation, if one exists
        :keyword db_filename: string. Sets the name of the sqlite3 database file. If
                              not specified, stored in memory.
        """
        self.verbose = kwargs.get("verbose")
        if not self.verbose != True:
            self.verbose == False

        self.__root = os.path.dirname(os.path.abspath(__file__))

        self.__file_path = os.path.join(self.__root, "data")

        self.__db_filename = kwargs.get("db_filename", ":memory:")
        
        if self.verbose:
            print("Database: {}".format(self.__db_filename))

        if kwargs.get("new_file") in (True, "yes") and self.__db_filename != ":memory:":
            if os.path.exists(self.__db_filename):
                os.remove(self.__db_filename)
        have_db = True

        if not os.path.exists(self.__db_filename) or self.__db_filename == ":memory:":
            have_db = False

        self.db = sqlite3.connect(self.__db_filename)
        if not have_db:
            self.__initialize()
        
        self._pattern      = None
        self._regex_pattern = re.compile("%[\w,=]+%")
        
    def __initialize(self):
        """
        Initializes database and copies data in from text files.
        """
        self.__init_name_last()
        self.__init_name_first()
        self.__init_country()
        self.__init_state()
        self.__init_zip()
        self.__init_area_code()
        self.__init_nickname()
        self.__init_street_suffix()
        self.__init_business_suffix()
        self.__init_company_word()
        self.__init_occupations()

    def __init_name_last(self):
        """
        Import last names.
        """
        if self.verbose:
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
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_lastname_lastname ON last_name(last_name)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "surnames.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline()     # Trash the header line
            reader = csv.reader(f_in)
            for row in reader:
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
                self.__exec_statement(sql, row)
            self.db.commit()

    def __init_name_first(self):
        """
        Import first names.
        """
        if self.verbose:
            print("Initializing first names...")
        sql = """
        CREATE TABLE first_name (
            first_name text NOT NULL,
            sex text NOT NULL
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_firstname_firstname ON first_name(first_name)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "firstname.csv")
        with open(input_file_name, "r") as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                sql = """
                INSERT INTO first_name (
                    first_name,
                    sex
                )
                VALUES (?, ?)
                """
                self.__exec_statement(sql, row)
            self.db.commit()

    def __init_country(self):
        """
        Import countries.
        """
        if self.verbose:
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
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_country_twoletter ON country(abbr_twoletter)")
        self.__exec_statement("CREATE INDEX idx_country_nameformal ON country(name_formal)")
        self.__exec_statement("CREATE INDEX idx_country_nameshort ON country(name_short)")
        self.__exec_statement("CREATE INDEX idx_country_fallback ON country(name_fallback)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "countries.csv")
        with open(input_file_name, "r") as f_in:
            f_in.readline()     # Get rid of the header line
            reader = csv.reader(f_in)
            for row in reader:
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
                self.__exec_statement(sql, row)
            self.db.commit()

    def __init_state(self):
        """
        Import states
        """
        if self.verbose:
            print("Initializing states...")
        sql = """
        CREATE TABLE state (
            name text PRIMARY KEY,
            abbreviation text,
            capital text,
            status integer
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_state_nam ON state(name)")
        self.__exec_statement("CREATE INDEX idx_state_abbr ON state(abbreviation)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "states.csv")

        with open(input_file_name) as f_in:
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
                self.__exec_statement(sql, row)
            self.db.commit()

    def __init_zip(self):
        """
        Import zip codes, cities, counties, and timezones.
        """
        if self.verbose:
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
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_zip_zip ON zip(zip)")
        self.__exec_statement("CREATE INDEX idx_zip_city ON zip(city)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "zip.csv")
        with open(input_file_name) as f_in:
            f_in.readline()
            reader = csv.reader(f_in)
            for row in reader:
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
                self.__exec_statement(sql, row)
            self.db.commit()
    
    def __init_area_code(self):
        """
        Import area codes.
        """
        if self.verbose:
            print("Initializing area codes...")
        sql = """
        CREATE TABLE area_code (
            code integer,
            city text,
            state text,
            country_code text
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_areacode_code ON area_code(code)")
        self.__exec_statement("CREATE INDEX idx_areacode_city ON area_code(city)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "area_codes.csv")
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
                self.__exec_statement(sql, row)
            self.db.commit()
    
    def __init_nickname(self):
        """
        Import nicknames.
        """
        if self.verbose:
            print("Initializing nicknames...")    
        sql = """
        CREATE TABLE nickname (
            nickname text NOT NULL PRIMARY KEY
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_nickname_nickname ON nickname(nickname)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "nicknames.txt")
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
                self.__exec_statement(sql, values)
            self.db.commit()

    def __init_street_suffix(self):
        """
        Import street suffixes.
        """
        if self.verbose:
            print("Initializing street suffixes")
        sql = """
        CREATE TABLE street_suffix (
            suffix text
        )
        """
        self.__exec_statement(sql)
        sql = """
        CREATE TABLE street_suffix_abbr (
            abbr text,
            suffix_id number
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_streetsuffix ON street_suffix(suffix)")
        self.__exec_statement("CREATE INDEX idx_streetsuffix_abbr ON street_suffix_abbr(abbr)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "street_suffixes.csv")
        with open(input_file_name, "r") as f_in:
            reader = csv.reader(f_in)
            for row in reader:
                root = row[0]
                abbrs = row[1:]

                sql = """INSERT INTO street_suffix (suffix) VALUES (?)"""
                values = (root,)
                self.__exec_statement(sql, values)

                for abbr in abbrs:
                    sql = """SELECT rowid FROM street_suffix WHERE suffix = ?"""
                    values = (root,)
                    rowid = self.__get_scalar(sql, values)
                    sql = """INSERT INTO street_suffix_abbr (abbr, suffix_id) VALUES (?, ?)"""
                    values = (abbr, rowid)
                    self.__exec_statement(sql, values)
            self.db.commit()

    def __init_business_suffix(self):
        """
        Import business suffixes.
        """
        if self.verbose:
            print("Initializing business suffixes...")
        sql = """
        CREATE TABLE business_suffix (
            suffix text
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_businesssuffix_suffix ON business_suffix(suffix)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "business_suffixes.txt")
        with open(input_file_name, "r") as f_in:
            for line in f_in:
                line = line.strip()
                sql = """INSERT INTO business_suffix (suffix) VALUES (?)"""
                values = (line,)
                self.__exec_statement(sql, values)                
            self.db.commit()

    def __init_company_word(self):
        """
        Import company words.  This is a dumb function.
        """
        if self.verbose:
            print("Initializing company words...")
        sql = """
        CREATE TABLE company_word (
            word text NOT NULL PRIMARY KEY UNIQUE
        )
        """
        self.__exec_statement(sql)
        self.__exec_statement("CREATE INDEX idx_companyword_word ON company_word(word)")
        self.db.commit()

        input_file_name = os.path.join(self.__file_path, "business_words.txt")

        with open(input_file_name, "r") as f_in:
            for line in f_in:
                line = line.strip()
                sql = "SELECT count(*) FROM company_word WHERE word = ?"
                values = (line,)
                data = self.__get_scalar(sql, values)

                if data == 0:
                    sql = "INSERT INTO company_word (word) VALUES (?)"
                    values = (line,)
                    self.__exec_statement(sql, values)
            self.db.commit()
    
    def __init_occupations(self):
        """
        Import occupations.
        """
        if self.verbose:
            print("Initializing occupations...")
            self.__exec_statement("CREATE TABLE occupation (occupation text NOT NULL PRIMARY KEY UNIQUE)")
            self.__exec_statement("CREATE INDEX idx_occupation_occupation ON occupation(occupation)")
            self.db.commit()

            input_file_name = os.path.join(self.__file_path, "occupations.txt")

            with open(input_file_name, "r") as f_in:
                for line in f_in:
                    line = line.strip()
                    sql = "SELECT count(*) FROM occupation WHERE occupation = ?"
                    values = (line,)
                    data = self.__get_scalar(sql, values)

                    if data == 0:
                        sql = "INSERT INTO occupation (occupation) VALUES (?)"
                        values = (line,)
                        self.__exec_statement(sql, values)
                self.db.commit()

    def __get_rows(self, sql, values=None):
        """
        Retrieves multiple rows from database
        :param sql: String containing SQL Request
        :param values: Tuple/List with values to substitute
        :return: List of lists containing all rows of data
        """
        cur = self.db.cursor()
        if values:
            cur.execute(sql, values)
        else:
            cur.execute(sql)
        return cur.fetchall()

    def __get_row(self, sql, values=None):
        """
        Retrieves a single row from database
        :param sql: String containing SQL Request
        :param values: Tuple/List with values to substitute
        :return: List containing 1 row of data
        """
        results = self.__get_rows(sql, values)
        if len(results) == 0:
            return results
        return results[0]

    def __get_scalar(self, sql, values=None):
        """
        Retrieves a single cell from database
        :param sql: String containing SQL Request
        :param values: Tuple/List with values to substitute
        :return: single datatype return
        """
        results = self.__get_row(sql, values)
        if len(results) == 0:
            return None
        return results[0]
    
    def __exec_statement(self, sql, values=None):
        """
        Executes an SQL Statement with no return.
        :param sql: String containing SQL Request
        :param values: Tuple/List with values to substitute
        """
        if values:
            self.__get_rows(sql, values)
        else:
            self.__get_rows(sql)
        return

    def firstname(self, sex=None, boy=False, girl=False):
        """
        Returns random first name.
        :param sex: boy/man/male or girl/woman/female
                    Sex of name to select. Random if none chosen.
        :param boy: boolean.  Return boy's name (mutually exclusive with girl)
        :param girl: boolean.  Return girl's name (mutually exclusive with boy)
        :return: String containing first name.
        """
        if isinstance(sex, str):
            if sex.lower() in ("boy", "man", "male"):
                boy = True
            elif sex.lower() in ("girl", "woman", "female"):
                girl = True
        if boy == True and girl == True:
            raise ValueError("Boy and Girl cannot both be true")

        max_rowid = self.__get_scalar("SELECT max(rowid) FROM first_name")

        name = None

        while not name:
            random_id = random.randint(1, max_rowid)
            sql = "SELECT first_name FROM first_name WHERE rowid = {}".format(random_id)

            if boy:
                sql += " AND sex = 'boy'"
            elif girl:
                sql += " AND sex = 'girl'"
            name = self.__get_scalar(sql)
        return name
    
    def lastname(self):
        """
        Returns random last name.
        :return: String containing last name.
        """
        max_rowid = self.__get_scalar("SELECT max(rowid) FROM last_name")
        random_id = random.randint(1, max_rowid)
        name = self.__get_scalar("SELECT last_name FROM last_name WHERE rowid = {}".format(random_id))
        if random.randint(1, 20) == 1:
            random_id = random.randint(1, max_rowid)
            name2 = self.__get_scalar("SELECT last_name FROM last_name WHERE rowid = {}".format(random_id))
            name = "{}-{}".format(name, name2)
        return self.__correct_case(name)
    
    def name_suffix(self):
        """
        Returns random name suffix.  Jr/Sr/I-X
        :return: String containing random suffix.
        """
        # 95% chance no suffix
        # 4% chance jr/sr (equal probability)
        # 1% chance Roman Numeral
        #   85% chance of 1-3
        #   10% chance of 4
        #   2% chance of 5
        #   1% - 6
        #   0.5% - 7
        #   0.5% - 8
        #   0.5% - 9
        #   0.5% - 10
        chance = random.randint(1, 100)
        if chance <= 95:
            return ""
        elif 95 < chance <= 99:
            return "Jr" if randint(0, 1) == 0 else "Sr"
        else:
            _romans = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
            chance2 = random.randint(1, 200)
            if chance2 <= 170:
                # 1-3 - 85%
                return _romans[random.randint(0, 3)]
            elif 170 < chance2 <= 190:
                return _romans[3]
            elif 190 < chance2 <= 194:
                return _romans[4]
            elif 194 < chance2 <= 196:
                return _romans[5]
            elif 196 < chance2 <= 197:
                return _romans[6]
            elif 197 < chance2 <= 198:
                return _romans[7]
            elif 198 < chance2 <= 199:
                return _romans[8]
            elif 199 < chance2 <= 200:
                return _romans[9]
        raise ValueError("Unexpected result in name_suffix()")

    def fullname(self, **kwargs):
        """
        Returns full name from random pieces.
        :keyword middle_initial: Boolean.  Include a middle initial or not
                                 Mutually exclusive with middle_name
        :keyword middle_name:    Boolean.  Include a middle name or not
                                 Mutually exclusive with middle_initial
        :keyword suffix:         Boolean.  Include a suffix or not
        :return:                 String name with format: <First> [MI|Middle] <Last> [Suffix]
        """
        _middle_initial = kwargs.get("middle_initial")
        if _middle_initial not in (True, False, None):
            raise ValueError("middle_initial value must be True/False")
        
        _middle_name = kwargs.get("middle_name")
        if _middle_name not in (True, False, None):
            raise ValueError("middle_name value must be True/False")
        
        if _middle_name and _middle_initial:
            raise ValueError("middle_name and middle_initial both specified. They are mutually exclusive.")
        
        _suffix = kwargs.get("suffix")
        if _suffix not in (True, False, None):
            raise ValueError("suffix value must be True/False")

        name = []
        name.append(self.firstname())
        if _middle_initial:
            name.append(self.middle_initial())
        if _middle_initial:
            name.append(self.firstname())
        name.append(self.lastname())
        if _suffix:
            name.append(self.name_suffix())
        return " ".join(name)

    def __correct_case_word(self, word):
        """
        Capitalizes the first letter of word, all the rest lowercase.
        :param word: String with word to capitalize.
        :return: String with corrected case.
        """
        return "{}{}".format(word[0].upper(), word[1:].lower())

    def __correct_case(self, word):
        """
        Capitalizes the first letter of a set of words, all the rest lowercase.
        :param word: String with words to capitalize.
        :return: String with corrected case.
        """
        words = word.split(" ")
        word = " ".join(self.__correct_case_word(_) for _ in words)
        words = word.split("-")
        word = "-".join(self.__correct_case_word(_) for _ in words)
        return word
    
    def age(self, **kwargs):
        """
        Generates a random age.
        :keyword category: String. Age category to use.
                           any          1-105
                           baby         0-1
                           infant       1-2
                           toddler      2-3
                           child        0-17
                           teen        13-19
                           young adult 18-25
                           adult       18-105
                           middle age  35-55
                           retired     65-105
        :return:           Integer with random age.
        """
        category        = kwargs.get("category")
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
    
    def state(self, **kwargs):
        """
        Returns random US State
        :param allow_territories: Boolean. Allows US Territories as possible return value. Default=True
        :param allow_military:    Boolean. Allows FPO addresses. Default=True
        :param allow_states:      Boolean. Allows standard states. Default=True
        :param long:              Return long state name.  Default=False
        :return:                  String with 2 character state abbreviation.
        """
        allow_territories = kwargs.get("allow_territories", True)
        allow_military    = kwargs.get("allow_military",    True)
        allow_states      = kwargs.get("allow_states",      True)
        long_name         = kwargs.get("long",              False)
        max_rowid = self.__get_scalar("SELECT max(rowid) FROM state")
        
        rowid = random.randint(1, max_rowid)
        _type = "name" if long_name else "abbreviation"
        sql = "SELECT {} FROM state WHERE rowid = {} AND status in (".format(_type, rowid)
        allows = []
        if allow_states:
            allows.append("0")
        if allow_military:
            allows.append("1")
        if allow_territories:
            allows.append("2")
        sql += ", ".join(allows)
        sql += ")"

        return self.__get_scalar(sql)
    
    def city(self, **kwargs):
        """
        Returns random city.
        :param state: String containing 2-letter state abbreviation to choose from.
        :return:      String with city, State
        """
        state = kwargs.get("state")
        max_rowid = self.__get_scalar("SELECT max(rowid) FROM zip")
        while True:
            rowid = random.randint(1, max_rowid)

            sql = "SELECT city, state_abbr FROM zip WHERE rowid = {}".format(rowid)
            if state and state_abbr != state:
                continue
            return ", ".join(self.__get_row(sql))

    def number(self, start=None, end=None, **kwargs):
        """
        Returns random number between 'start' and 'end'
        :param start:   Range start
        :param end:     Range end
        :keyword start: Range start
        :keyword end:   Range end
        :return:        Int of random number
        """
        if start and kwargs.get("start"):
            raise ValueError("Cannot specify start range and 'start' keyword.")
        if end and kwargs.get("end"):
            raise ValueError("Cannot specify end range and 'end' keyword.")
        start = kwargs.get("start", start)
        end   = kwargs.get("end",   end)
        if not end:
            end = start
            start = 1
        
        return random.randint(start, end)
    
    def money(self, start=None, end=None, **kwargs):
        """
        Returns random number between 'start' and 'end'
        :param start:   Range start
        :param end:     Range end
        :keyword start: Range start
        :keyword end:   Range end
        :return:        Int of random number
        """
        if start and kwargs.get("start"):
            raise ValueError("Cannot specify start range and 'start' keyword.")
        if end and kwargs.get("end"):
            raise ValueError("Cannot specify end range and 'end' keyword.")
        start = kwargs.get("start", start)
        end   = kwargs.get("end",   end)

        if not end:
            end = start
            start = 0.00
        
        start *= 100
        end *= 100

        number = random.randint(start, end)
        return number / 100
    
    def occupation(self):
        """
        Returns random occupation
        :return: String containing random occupation
        """
        max_rowid = self.__get_scalar("SELECT max(rowid) FROM occupation")
        while True:
            rowid = random.randint(1, max_rowid)

            sql = "SELECT occupation FROM occupation WHERE rowid = ?"
            values = (rowid,)
            data = self.__get_scalar(sql, values)
            if not data:
                continue
            return data
    
    def __company_word(self):
        """
        Returns company word.
        :return: String containing company word.
        """
        max_rowid = self.__get_scalar("SELECT max(rowid) FROM company_word")
        while True:
            rowid = random.randint(1, max_rowid)

            sql = "SELECT word FROM company_word WHERE rowid = ?"
            values = (rowid,)
            data = self.__get_scalar(sql, values)
            if not data:
                continue
            return data

    def _and(self):
        """
        Returns random & or 'and'
        :return: String with & or 'and'
        """
        return "&" if random.randint(0, 1) == 0 else "and"
    
    def _son(self):
        """
        Returns random variant of 'son'
        :return: String containing <son|Son>[s]
        """
        tmp = ""
        if random.randint(0, 1) == 0:
            tmp += "son"
        else:
            tmp += "Son"
        if random.randint(0, 1) == 0:
            tmp += "s"
            
        return tmp

    def _letter(self):
        """
        Returns random letter.
        :return: String containing random lowercase letter.
        """
        _int = random.randint(0, len(string.ascii_lowercase))
        letter = string.ascii_lowercase[_int]
    
    def _initial(self):
        """
        Random initial.
        :return: String containing <upper-case letter>[.]
        """
        initial = self._letter().upper()
        if random.randint(0, 1) == 0:
            initial += "."
        return initial

    def company_name(self):
        """
        Returns random company name.
        :return: String containing company name.
        """
        # Company Name
        # Company Suffix
        # Types:
        #   1 Name[, Name]<&|and> Name [suffix]
        #   2 Name <&|son[s]> [suffix]
        #   3 SingleName, Esq
        #   4 name <ing> [inc, llc]
        #   5 name's <type> [suffix]
        #   5 names' <type> [suffix]
        name = ""
        
        _type = random.randint(1, 5)
        if _type == 1:
            max_words = 3
            words_to_get = random.randint(1, max_words)
            words = [self.lastname() for _ in range(words_to_get)]
            if len(words) == 1:
                name = words[0]
            elif len(words) == 2:
                name = "{} {} {}".format(words[0], self._and(), words[1])
            elif len(words) >= 3:
                name = ", ".join(words[:-1]) + " {} ".format(self._and()) + words[-1]
        
        elif _type == 2:
            name = None
            # First (0) or last (1) name?
            _first_last = random.randint(0, 1)
            if _first_last == 0:
                name = self.firstname()
            else:
                name = self.lastname()
            name += " " + self._and() + " " + self._son()  

        elif _type == 3:
            name = self.fullname() + ", Esq"

        else:
            name = "Undefined"
        return name
    
    def set_pattern(self, **kwargs):
        """
        Sets the output pattern for resulting data.
        :keyword pattern: String containing the output pattern.
        """
        pattern      = kwargs.get("pattern")
        if pattern:
            self._pattern = pattern

    def get_line(self, **kwargs):
        """
        Gets a line based on a provided pattern.  Pattern can be set with either set_pattern() or passed into this function.
        :keyword pattern: String containing pattern of the output line.
        :return: String
        """
        line = kwargs.get("pattern", self._pattern)

        while True:
            _tmp         = self._regex_pattern.search(line)
            if not _tmp:
                break
            _word        = _tmp.group(0)[1:-1]
            _kwargs      = {}
            while "," in _word:
                _wordsplit = _word.split(",")
                _tmp2                        = _wordsplit[1]
                _kwargs[_tmp2.split("=")[0]] = _tmp2.split("=")[1]
                if len(_wordsplit) >= 3:
                    _word                       = "{},{}".format(_wordsplit[0], ",".join(_wordsplit[2:]))
                else:
                    _word = _wordsplit[0]
            _os1, _os2   = _tmp.span()
            _first       = line[:_os1]
            _last        = line[_os2:]
            _middle      = getattr(self, _word)(**_kwargs)
            line         = "{}{}{}".format(_first, _middle, _last)
        return line

