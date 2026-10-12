"""Seed the database with demo data for development and evaluation."""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from billing.models import Invoice, InvoiceItem, Payment
from clinical.models import MedicalRecord
from laboratory.models import LabOrder, LabTest
from patients.models import Patient
from pharmacy.models import Medicine, PharmacySale
from scheduling.models import Appointment, Doctor
from wards.models import Admission, Bed, Ward

random.seed(42)
TODAY = timezone.localdate()

FIRST = ["James", "Mary", "John", "Grace", "Peter", "Faith", "David", "Sarah", "Michael",
         "Esther", "Daniel", "Ruth", "Samuel", "Hannah", "Joseph", "Rebecca", "Brian",
         "Cynthia", "George", "Lydia", "Francis", "Mercy", "Stephen", "Agnes", "Kevin"]
LAST = ["Mwangi", "Achieng", "Otieno", "Wanjiku", "Kamau", "Njeri", "Ochieng", "Atieno",
        "Kiptoo", "Chebet", "Maina", "Wambui", "Ouma", "Nyambura", "Kariuki", "Auma",
        "Barasa", "Wafula", "Mutiso", "Syombua", "Kiprop", "Jelimo", "Njoroge", "Waithera"]
BLOOD = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class Command(BaseCommand):
    help = "Seed demo data (idempotent-ish: clears demo tables first)."

    def handle(self, *args, **options):
        with transaction.atomic():
            self._clear()
            users = self._users()
            doctors = self._doctors()
            patients = self._patients()
            wards = self._wards()
            medicines = self._medicines()
            tests = self._lab_tests()
            self._admissions(patients, doctors, wards, users)
            self._appointments(patients, doctors, users)
            self._records(patients, doctors, users)
            self._lab_orders(patients, tests, users)
            self._pharmacy_sales(patients, medicines, users)
            self._invoices(patients, users)
        self.stdout.write(self.style.SUCCESS("Demo data seeded."))

    def _clear(self):
        for model in [Payment, InvoiceItem, Invoice, PharmacySale, LabOrder,
                      MedicalRecord, Appointment, Admission, Bed, Ward,
                      Medicine, LabTest, Doctor, Patient]:
            model.objects.all().delete()
        User.objects.filter(username__in=["admin", "doctor1", "recep", "pharm", "lab"]).delete()

    def _users(self):
        specs = [
            ("admin", "admin123", "System", "Administrator", "admin"),
            ("doctor1", "doc123", "Alice", "Doctor", "doctor"),
            ("recep", "recep123", "Rita", "Receptionist", "receptionist"),
            ("pharm", "pharm123", "Paul", "Pharmacist", "pharmacist"),
            ("lab", "lab123", "Lydia", "Labtech", "labtech"),
        ]
        users = {}
        for username, password, first, last, role in specs:
            u = User(username=username, first_name=first, last_name=last,
                     email=f"{username}@hospital.local", role=role, is_active=True)
            u.set_password(password)
            u.save()
            users[username] = u
        return users

    def _doctors(self):
        specs = [
            ("John", "Kimani", "Cardiology", 2500),
            ("Susan", "Achieng", "Pediatrics", 2000),
            ("Peter", "Njoroge", "Orthopedics", 2200),
            ("Mary", "Wanjiru", "Gynecology", 2000),
            ("David", "Odhiambo", "General Medicine", 1500),
            ("Grace", "Muthoni", "Dermatology", 1800),
        ]
        return [Doctor.objects.create(first_name=f, last_name=l, specialization=s,
                                      consultation_fee=fee, phone=f"0722{random.randint(100000,999999)}")
                for f, l, s, fee in specs]

    def _patients(self):
        patients = []
        for i in range(25):
            first, last = random.choice(FIRST), random.choice(LAST)
            age = random.randint(1, 85)
            dob = TODAY - timedelta(days=age * 365 + random.randint(0, 364))
            patients.append(Patient(
                first_name=first, last_name=last, dob=dob,
                gender=random.choice(["M", "F"]),
                phone=f"07{random.randint(10,99)}{random.randint(100000,999999)}",
                email=f"{first.lower()}.{last.lower()}{i}@example.com",
                address=f"{random.randint(1,999)} {random.choice(['Kenyatta Ave','Moi Ave','Ngong Rd','Thika Rd'])}, Nairobi",
                blood_group=random.choice(BLOOD),
                allergies=random.choice(["", "", "Penicillin", "Sulfa drugs", "Peanuts"]),
            ))
        Patient.objects.bulk_create(patients)
        # bulk_create skips save(), so backfill the auto patient numbers.
        for p in Patient.objects.filter(patient_no__isnull=True):
            p.patient_no = f"P-{p.pk:04d}"
            p.save(update_fields=["patient_no"])
        return list(Patient.objects.all())

    def _wards(self):
        specs = [("General Ward A", "general", 10), ("General Ward B", "general", 10),
                 ("Pediatric Ward", "pediatric", 8), ("Maternity Ward", "maternity", 8),
                 ("ICU", "icu", 4), ("Private Wing", "private", 6)]
        wards = []
        for name, wtype, cap in specs:
            ward = Ward.objects.create(name=name, ward_type=wtype, capacity=cap)
            beds = [Bed(ward=ward, bed_no=f"{name.split()[0][:3].upper()}-{i+1:02d}")
                    for i in range(cap)]
            Bed.objects.bulk_create(beds)
            wards.append(ward)
        return wards

    def _medicines(self):
        specs = [
            ("Paracetamol 500mg", "Analgesic", "tablet", 850, 100, 5, 400),
            ("Amoxicillin 250mg", "Antibiotic", "capsule", 420, 100, 12, 700),
            ("Ibuprofen 400mg", "Analgesic", "tablet", 60, 100, 8, 500),
            ("Metformin 500mg", "Antidiabetic", "tablet", 300, 80, 15, 800),
            ("Lisinopril 10mg", "Antihypertensive", "tablet", 25, 50, 20, 750),
            ("Omeprazole 20mg", "Antacid", "capsule", 500, 100, 10, 600),
            ("Cetirizine 10mg", "Antihistamine", "tablet", 700, 100, 6, 900),
            ("Azithromycin 500mg", "Antibiotic", "tablet", 15, 60, 45, 300),
            ("Hydrochlorothiazide 25mg", "Diuretic", "tablet", 200, 60, 9, 650),
            ("Salbutamol Inhaler", "Respiratory", "inhaler", 90, 30, 350, 200),
            ("Insulin Glargine", "Antidiabetic", "vial", 40, 20, 1200, 120),
            ("Ciprofloxacin 500mg", "Antibiotic", "tablet", 350, 80, 18, 550),
            ("Diclofenac Gel", "Topical", "tube", 120, 40, 250, 250),
            ("ORS Sachets", "Rehydration", "sachet", 1000, 200, 30, 1500),
            ("Artemether-Lumefantrine", "Antimalarial", "tablet", 8, 50, 60, 250),
            ("Fluconazole 150mg", "Antifungal", "capsule", 180, 50, 35, 400),
            ("Prednisolone 5mg", "Steroid", "tablet", 260, 60, 7, 500),
            ("Losartan 50mg", "Antihypertensive", "tablet", 140, 60, 22, 450),
            ("Vitamin B Complex", "Supplement", "tablet", 900, 150, 4, 1200),
            ("Gauze Roll", "Consumable", "roll", 300, 100, 50, 400),
        ]
        medicines = []
        for i, (name, cat, unit, qty, reorder, price, days_to_expiry) in enumerate(specs):
            expiry = TODAY + timedelta(days=days_to_expiry)
            if i % 7 == 3:  # a couple near-expiry items
                expiry = TODAY + timedelta(days=random.randint(10, 45))
            medicines.append(Medicine(name=name, category=cat, unit=unit,
                                      quantity_in_stock=qty, reorder_level=reorder,
                                      unit_price=Decimal(price), expiry_date=expiry))
        Medicine.objects.bulk_create(medicines)
        return list(Medicine.objects.all())

    def _lab_tests(self):
        specs = [
            ("Full Blood Count", "Hematology", 800), ("Blood Sugar (Fasting)", "Biochemistry", 400),
            ("HIV Test", "Serology", 500), ("Malaria RDT", "Parasitology", 350),
            ("Urinalysis", "Biochemistry", 300), ("Liver Function Test", "Biochemistry", 1500),
            ("Kidney Function Test", "Biochemistry", 1400), ("X-Ray Chest", "Imaging", 2000),
            ("Ultrasound Abdomen", "Imaging", 2500), ("Pregnancy Test", "Serology", 300),
            ("Typhoid Test (Widal)", "Serology", 600), ("Stool Analysis", "Parasitology", 450),
        ]
        return [LabTest.objects.create(name=n, category=c, price=Decimal(p)) for n, c, p in specs]

    def _admissions(self, patients, doctors, wards, users):
        beds = list(Bed.objects.filter(status=Bed.STATUS_AVAILABLE))
        random.shuffle(beds)
        for i in range(5):
            bed = beds.pop()
            bed.status = Bed.STATUS_OCCUPIED
            bed.save(update_fields=["status"])
            Admission.objects.create(
                patient=random.choice(patients), bed=bed, doctor=random.choice(doctors),
                admit_date=TODAY - timedelta(days=random.randint(0, 6)),
                diagnosis=random.choice(["Pneumonia", "Malaria", "Fracture - left tibia",
                                         "Post-cesarean observation", "Severe dehydration"]),
                admitted_by=users["recep"],
            )

    def _appointments(self, patients, doctors, users):
        slots = [(9, 0), (10, 0), (11, 0), (12, 0), (14, 0), (15, 0)]
        used = set()
        for i in range(15):
            doctor = random.choice(doctors)
            day_offset = random.choice([-1, 0, 0, 1, 2, 3])
            appt_date = TODAY + timedelta(days=day_offset)
            hour, minute = random.choice(slots)
            key = (doctor.pk, appt_date, hour, minute)
            if key in used:
                continue
            used.add(key)
            status = "scheduled"
            if day_offset < 0:
                status = random.choice(["completed", "completed", "no_show"])
            Appointment.objects.create(
                patient=random.choice(patients), doctor=doctor,
                appt_date=appt_date,
                appt_time=f"{hour:02d}:{minute:02d}",
                reason=random.choice(["General checkup", "Follow-up visit", "Fever and headache",
                                      "Prenatal visit", "Skin rash", "Joint pain"]),
                status=status, created_by=users["recep"],
            )

    def _records(self, patients, doctors, users):
        diags = [("Acute malaria", "Artemether-Lumefantrine 4 tablets twice daily x3 days"),
                 ("Upper respiratory infection", "Amoxicillin 250mg 3x daily x5 days"),
                 ("Hypertension", "Lisinopril 10mg once daily; review in 1 month"),
                 ("Type 2 diabetes", "Metformin 500mg twice daily; diet counseling"),
                 ("Gastritis", "Omeprazole 20mg once daily x14 days")]
        for _ in range(10):
            d, rx = random.choice(diags)
            MedicalRecord.objects.create(
                patient=random.choice(patients), doctor=random.choice(doctors),
                visit_date=TODAY - timedelta(days=random.randint(0, 20)),
                diagnosis=d, prescription=rx,
                notes="Patient counseled on medication adherence.",
                created_by=users["doctor1"],
            )

    def _lab_orders(self, patients, tests, users):
        for _ in range(10):
            order = LabOrder.objects.create(
                patient=random.choice(patients), test=random.choice(tests),
                ordered_by=users["lab"],
            )
            if random.random() < 0.6:
                order.status = LabOrder.STATUS_COMPLETED
                order.result_text = "Within normal limits. See attached report."
                order.completed_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                order.save()

    def _pharmacy_sales(self, patients, medicines, users):
        for _ in range(12):
            med = random.choice(medicines)
            qty = random.randint(1, 5)
            if med.quantity_in_stock < qty:
                continue
            med.quantity_in_stock -= qty
            med.save(update_fields=["quantity_in_stock"])
            total = med.unit_price * Decimal(qty)
            sale = PharmacySale.objects.create(
                patient=random.choice(patients), medicine=med, quantity=qty,
                unit_price=med.unit_price, total=total, sold_by=users["pharm"],
            )
            invoice = Invoice.objects.create(patient=sale.patient, subtotal=total,
                                             total=total, created_by=users["pharm"])
            InvoiceItem.objects.create(invoice=invoice,
                                       description=f"{med.name} × {qty} {med.unit}",
                                       quantity=Decimal(qty), unit_price=med.unit_price,
                                       line_total=total)

    def _invoices(self, patients, users):
        services = [("Consultation fee", 1500), ("X-Ray Chest", 2000),
                    ("Full Blood Count", 800), ("Ultrasound Abdomen", 2500),
                    ("Dressing change", 500), ("IV fluids + nursing", 1200)]
        for i in range(8):
            patient = random.choice(patients)
            n_items = random.randint(1, 3)
            chosen = random.sample(services, n_items)
            subtotal = sum(Decimal(p) for _, p in chosen)
            discount = Decimal(random.choice([0, 0, 100, 200]))
            tax = Decimal("0")
            total = subtotal - discount
            invoice = Invoice.objects.create(
                patient=patient, subtotal=subtotal, discount=discount, tax=tax,
                total=total, issue_date=TODAY - timedelta(days=random.randint(0, 10)),
                created_by=users["recep"],
            )
            for desc, price in chosen:
                InvoiceItem.objects.create(invoice=invoice, description=desc,
                                           quantity=Decimal("1"),
                                           unit_price=Decimal(price),
                                           line_total=Decimal(price))
            # Some payments: a few fully paid, some partial.
            r = random.random()
            if r < 0.4:
                Payment.objects.create(invoice=invoice, amount=total, method="cash",
                                       received_by=users["recep"])
                invoice.amount_paid = total
            elif r < 0.7:
                part = (total // 2).quantize(Decimal("1"))
                Payment.objects.create(invoice=invoice, amount=part, method="mpesa",
                                       received_by=users["recep"])
                invoice.amount_paid = part
            invoice.refresh_status()
            invoice.save(update_fields=["amount_paid", "status"])
