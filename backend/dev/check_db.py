from src.services.database_service import DatabaseService

db = DatabaseService()
db.initialize()

collections = db.list_collections()
print('All collections:', collections)

for col in collections:
    count = db.count_documents(col)
    print(f'{col}: {count} documents')
    
    # Show sample data for each collection
    if count > 0:
        sample = db.find_many(col, limit=1)
        if sample:
            print(f'  Sample from {col}:', list(sample[0].keys()))
        print()