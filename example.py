from data_creator import DataCreator

def main():
    dc = DataCreator(verbose=True, db_filename="/tmp/faker.db")

    print("First name: {}".format(dc.firstname(boy=True)))
    print("Last name:  {}".format(dc.lastname()))
    print("Age:        {}".format(dc.age()))
    print("Teenage:    {}".format(dc.age(category="teen")))
    print("State:      {}".format(dc.state()))
    print("City:       {}".format(dc.city()))
    print("Money:      {}".format(dc.money(100)))

    print()
    print("Company:    {}".format(dc.company_name()))
    print("get_line:")
    print(dc.get_line(pattern='"%firstname%","%lastname%","%occupation%","%age,category=teen%"'))
    print(dc.get_line(pattern="foo bar baz"))

if __name__ == "__main__":
    main()
