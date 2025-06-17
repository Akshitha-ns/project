import json

class Complaint:
    def __init__(self, id, student_name, description):
        self.id = id
        self.student_name = student_name
        self.description = description
        self.status = "Pending"

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.student_name,
            "description": self.description,
            "status": self.status
        }
    def from_dict(data):
        complaint = Complaint(data['id'], data['student_name'], data['description'])
        complaint.status = data['status']
        return complaint

class ComplaintManagementSystem:
    def __init__(self):
        self.complaints = []

    def add_complaint(self, complaint):
        self.complaints.append(complaint)

    def display_complaints(self):
        if not self.complaints:
            print("No complaints to display.")
            return
        for complaint in self.complaints:
            print(f"ID: {complaint.id}, Name: {complaint.student_name}, "
                  f"Description: {complaint.description}, Status: {complaint.status}")

    def process_complaint(self, complaint_id):
        for complaint in self.complaints:
            if complaint.id == complaint_id:
                complaint.status = "Processed"
                print(f"Complaint {complaint_id} marked as processed.")
                return
        print("Complaint ID not found.")

    def search_complaint_by_name(self, name):
        found = [c for c in self.complaints if c.student_name.lower() == name.lower()]
        if not found:
            print("No complaints found for this name.")
        else:
            for c in found:
                print(f"ID: {c.id}, Name: {c.student_name}, Description: {c.description}, Status: {c.status}")

    def save_to_file(self, filename):
        with open(filename, 'w') as file:
            json.dump([c.to_dict() for c in self.complaints], file)
        print("Complaints saved successfully.")

    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as file:
                data = json.load(file)
                self.complaints = [Complaint.from_dict(item) for item in data]
            print("Complaints loaded successfully.")
        except FileNotFoundError:
            print("No saved file found. Starting fresh.")

def menu():
    cms = ComplaintManagementSystem()
    cms.load_from_file("complaints.json")

    while True:
        print("\n==== Complaint Management System ====")
        print("1. Add Complaint")
        print("2. Display Complaints")
        print("3. Process Complaint")
        print("4. Search by Student Name")
        print("5. Save and Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            id = int(input("Enter complaint ID: "))
            name = input("Enter student name: ")
            description = input("Enter complaint description: ")
            complaint = Complaint(id, name, description)
            cms.add_complaint(complaint)
            print("Complaint added successfully.")

        elif choice == '2':
            cms.display_complaints()

        elif choice == '3':
            id = int(input("Enter complaint ID to process: "))
            cms.process_complaint(id)

        elif choice == '4':
            name = input("Enter student name to search: ")
            cms.search_complaint_by_name(name)

        elif choice == '5':
            cms.save_to_file("complaints.json")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    menu()
