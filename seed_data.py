"""
seed_data.py
Populates the database with realistic sample complaints so the dashboard,
charts and resolution-time statistics have something to show immediately.
Run once: python seed_data.py
"""

import random
from datetime import datetime, timedelta
from complaint_manager import ComplaintManager

SAMPLE_COMPLAINTS = [
    ("There is a large water leak near the main road and traffic is becoming difficult.", "Main Road, Sector 4", "Ayesha Khan", "0300-1234567"),
    ("Streetlight outside house number 12 has been off for a week, very dark and unsafe at night.", "Elm Street, Block B", "Bilal Ahmed", "0301-2345678"),
    ("Garbage bin near the market has been overflowing for three days, smell is unbearable.", "Central Market", "Sana Malik", "0302-3456789"),
    ("Big pothole on the highway is causing accidents, cars are swerving dangerously.", "Highway 9", "Usman Tariq", "0303-4567890"),
    ("Power outage in the whole colony since this morning, transformer seems to be sparking.", "Green Colony", "Hina Riaz", "0304-5678901"),
    ("Drainage is blocked and sewage is flooding onto the street after rain.", "Rose Avenue", "Farhan Iqbal", "0305-6789012"),
    ("Stray dogs are becoming aggressive near the school, parents are worried about children.", "Near Public School", "Zara Hussain", "0306-7890123"),
    ("No water supply for the last four days in our building, urgent need.", "Sunrise Apartments", "Ahmed Raza", "0307-8901234"),
    ("A tree fell and blocked the footpath after the storm last night.", "Park Lane", "Mahnoor Aslam", "0308-9012345"),
    ("Broken pavement tiles near the bus stop, several people have tripped.", "Bus Stand Road", "Kamran Shah", "0309-0123456"),
    ("Electric wire hanging low near the playground, looks extremely dangerous, kids play there.", "Community Playground", "Nida Farooq", "0311-1234567"),
    ("Trash collection has been missed for two weeks in our street.", "Willow Street", "Waqas Sheikh", "0312-2345678"),
    ("Water pipe burst is flooding the basement of our building.", "Riverside Complex", "Rabia Yousaf", "0313-3456789"),
    ("Street light pole is leaning and about to collapse onto the road.", "Market Road", "Imran Baig", "0314-4567890"),
    ("Waste dumping near the river bank is polluting the water badly.", "Riverbank Area", "Sara Nawaz", "0315-5678901"),
    ("Small crack developing on the footpath, not urgent but should be noted.", "Quiet Lane", "Adeel Chaudhry", "0316-6789012"),
    ("Minor delay in garbage pickup this week, one day late.", "Maple Street", "Mehwish Anwar", "0317-7890123"),
]


def run():
    manager = ComplaintManager()
    samples = SAMPLE_COMPLAINTS[:]
    random.shuffle(samples)

    for desc, loc, name, phone in samples:
        complaint = manager.submit_complaint(desc, loc, name, phone, image_flag=random.choice([True, False]))

        submit_dt = datetime.utcnow() - timedelta(days=random.randint(1, 20), hours=random.randint(0, 23))
        manager.db.update_dates(complaint.complaint_id, date=submit_dt.isoformat())

        if random.random() < 0.6:
            status = random.choice(["Assigned", "In Progress", "Resolved", "Resolved"])
            if status == "Resolved":
                resolved_dt = submit_dt + timedelta(hours=random.randint(3, 96))
                manager.db.update_status(complaint.complaint_id, status, resolved_date=resolved_dt.isoformat())
            else:
                manager.db.update_status(complaint.complaint_id, status)

    print(f"Seeded {len(samples)} sample complaints.")


if __name__ == "__main__":
    run()
