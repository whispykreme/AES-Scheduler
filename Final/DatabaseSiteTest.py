from Final.Main import *


def main():
    _path = 'OldResources/Resources.db'
    db = QSqlDatabase.addDatabase('QSQLITE')
    db.setDatabaseName(_path)
    db.open()

    tablemodel = QSqlRelationalTableModel(db=db)
    tablemodel.setTable("Deliveries")
    tablemodel.setRelation(tablemodel.fieldIndex("vcc"), QSqlRelation("Vcc", "id", "vcc"))
    tablemodel.setRelation(tablemodel.fieldIndex("county"), QSqlRelation("Counties", "id", "county"))
    tablemodel.setRelation(tablemodel.fieldIndex("driver"), QSqlRelation("Aes_Employees", "id", "name"))
    tablemodel.setRelation(tablemodel.fieldIndex("printer"), QSqlRelation("Printers", "id", "printer"))
    tablemodel.setRelation(tablemodel.fieldIndex("vehicle"), QSqlRelation("Vehicles", "id", "vehicle"))
    tablemodel.setRelation(tablemodel.fieldIndex("site"), QSqlRelation("Sites", "id", "site"))
    tablemodel.submit()

    # Get all site records
    # Turn county names into county ids
    # pass into make_records

    site_query = QSqlQuery()
    site_query.exec_("select id, county, site from Sites")

    sites = []
    while site_query.next():
        site_dict = {'id': site_query.value('id'),
                     'county': site_query.value('county'),
                     'site': site_query.value('site')}
        sites.append(site_dict)

    for site in sites:
        county_id_query = QSqlQuery()
        county_id_query.exec_(f"select id from Counties where county = '{site['county']}'")

        sites_id_query = QSqlQuery()
        sites_id_query.exec_(f"select id from Sites where site = '{site['site']}'")

        if county_id_query.first():
            site['county'] = county_id_query.value('id')

        if sites_id_query.first():
            site['site'] = sites_id_query.value('id')

    for site in sites:
        county_id = site['county']
        site_id = site['id']
        record = make_records(tablemodel, county_id, site_id)
        #print(record)
        #tablemodel.insertRecord(-1, record)
        tablemodel.insertRowIntoTable(record)

    print("Done")


def make_records(model, county_id, site_id):
    record = model.record()
    record.setGenerated('id', True)
    record.setValue('icon', 'icons\\box_truck.png')
    record.setValue('color', '#ffffff')
    record.setValue('vcc', 2)
    record.setValue('county', county_id)
    record.setValue('site', site_id)
    record.setValue('name', 0)
    record.setValue('printer', 2)
    record.setValue('quantity', 0)
    record.setValue('delivery_date', '5/11/2021')
    record.setValue('vehicle', 0)
    record.setValue('notes', '')
    return record


if __name__ == "__main__":
    main()