import frappe
from frappe.model.document import Document
from frappe import whitelist
import io
import re
import pdfplumber
import docx
from datetime import datetime, date

class ResumeUpload(Document):

    @whitelist()
    def parse_resumes(self):
        if not self.resume:
            self.status = "Failed: No resume file"
            self.save(ignore_permissions=True)
            frappe.throw("Please upload a resume file before parsing.")

        try:
            file_doc = frappe.get_doc("File", {"file_url": self.resume})
            if file_doc.is_private and file_doc.file_url.startswith("/files/"):
                file_doc.file_url = "/private" + file_doc.file_url
            file_content = file_doc.get_content()
        except Exception as e:
            self.status = "Failed: Cannot read file"
            self.save(ignore_permissions=True)
            frappe.throw(f"Could not read resume file. Reason: {e}")

        parsed_text = ""
        try:
            if self.resume.lower().endswith(".pdf"):
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    parsed_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            elif self.resume.lower().endswith(".docx"):
                doc = docx.Document(io.BytesIO(file_content))
                parsed_text = "\n".join(para.text for para in doc.paragraphs)
            else:
                self.status = "Failed: Unsupported file format"
                self.save(ignore_permissions=True)
                frappe.throw("Unsupported resume file format. Please upload PDF or DOCX.")
        except Exception as e:
            self.status = "Failed: Error parsing file"
            self.save(ignore_permissions=True)
            frappe.throw(f"Error parsing resume: {e}")

        parsed_text = re.sub(r'\n\s*\n', '\n', parsed_text).strip()

        email = self.extract_email(parsed_text)
        phone = self.extract_phone(parsed_text)
        linkedin = self.extract_linkedin(parsed_text)
        name = self.extract_name(parsed_text, fallback_name=self.name)
        dob = self.extract_dob(parsed_text)
        address = self.extract_address(parsed_text)
        education = self.extract_education(parsed_text)
        experience = self.extract_experience(parsed_text)  # UPDATED robust parsing

        if not email:
            self.status = "Failed: Email not found"
            self.save(ignore_permissions=True)
            frappe.msgprint("⚠️ Could not extract email from resume.")
            return

        try:
            applicant = frappe.new_doc("Job Applicant")
            applicant.applicant_name = name
            applicant.email_id = email
            applicant.phone_number = phone
            applicant.job_title = self.job_title
            applicant.source = "Agency"
            applicant.custom_agency_name = self.agency or ""
            applicant.custom_linkedin_profile_url = linkedin
            applicant.custom_date_of_birth = dob
            applicant.custom_applicant_address = address
            applicant.custom_parsed_resume = parsed_text[:100000]
            applicant.resume_attachment = self.resume

            for edu in education:
                applicant.append("custom_education_detail", edu)

            for exp in experience:
                applicant.append("custom_work_experience_deatils", exp)

            applicant.insert(ignore_permissions=True)

            self.status = f"Success: Job Applicant '{name}' created"
            self.save(ignore_permissions=True)

            frappe.msgprint(
                f"""✅ <a href="/app/job-applicant/{applicant.name}" target="_blank">
                Job Applicant '{name}' created</a>""",
                title="Success",
                indicator="green"
            )

        except Exception as e:
            self.status = f"Failed to create Job Applicant: {e}"
            self.save(ignore_permissions=True)
            frappe.throw(f"Failed to create Job Applicant: {e}")

    # === Extractors ===

    @staticmethod
    def extract_email(text):
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        return match.group(0).strip() if match else ""

    @staticmethod
    def extract_phone(text):
        match = re.search(r'(\+?\d[\d\s-]{9,14})', text)
        return match.group(0).strip() if match else ""

    @staticmethod
    def extract_linkedin(text):
        match = re.search(r'https?://(?:www\.)?linkedin\.com/(in|pub)/[^\s,]+', text)
        return match.group(0).strip() if match else ""

    @staticmethod
    def extract_name(text, fallback_name=None):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for i in range(min(5, len(lines))):
            line = lines[i]
            if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){1,3}$', line):
                return line
        for i, line in enumerate(lines):
            if '@' in line and i > 0:
                name_line = lines[i - 1].strip()
                if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+){0,3}$', name_line):
                    return name_line
        return fallback_name or "Unknown"

    @staticmethod
    def extract_dob(text):
        patterns = [
            r'\b(\d{2}[/-]\d{2}[/-]\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b',
            r'\b(\d{1,2} [A-Za-z]+ \d{4})\b'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d %B %Y"):
                    try:
                        return datetime.strptime(match.group(1).replace('/', '-'), fmt).date()
                    except:
                        continue
        return None

    @staticmethod
    def extract_address(text):
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if any(k in line.lower() for k in ["address", "resides at"]):
                address = line.strip()
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if len(next_line) > 10:
                        address += ", " + next_line
                return address
        return ""

    @staticmethod
    def extract_education(text):
        edu_list = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        patterns = [
            (r"(ssc|10th|secondary)", "Secondary School"),
            (r"(hsc|12th|higher secondary)", "Higher Secondary"),
            (r"(bachelor|graduation|b\.?tech|b\.?sc|b\.?com|bca)", "Graduation"),
            (r"(master|post graduation|m\.?tech|m\.?sc|m\.?com|mca)", "Post Graduation")
        ]

        for i, line in enumerate(lines):
            line_lower = line.lower()
            degree_type = None
            for pat, level in patterns:
                if re.search(pat, line_lower):
                    degree_type = level
                    break
            if not degree_type:
                continue

            edu = {
                "institution_name": line[:140],
                "degree_type": degree_type,
                "major": "",
                "start_date": None,
                "end_date": None
            }

            for j in range(i, min(i + 3, len(lines))):
                year_matches = re.findall(r"(19|20)\d{2}", lines[j])
                if year_matches:
                    try:
                        edu["end_date"] = datetime.strptime(year_matches[-1], "%Y").date()
                    except:
                        pass
                    if len(year_matches) > 1:
                        try:
                            edu["start_date"] = datetime.strptime(year_matches[0], "%Y").date()
                        except:
                            pass
                    break

            edu_list.append(edu)

        return edu_list

    @staticmethod
    def extract_experience(text):
        exp_list = []
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # Find start of work experience section
        start = None
        for i, line in enumerate(lines):
            if "work experience" in line.lower():
                start = i
                break
        if start is None:
            return exp_list

        # Stop at next section
        section_end = len(lines)
        for j in range(start + 1, len(lines)):
            if any(h in lines[j].lower() for h in ["education", "skills", "projects", "certification", "summary"]):
                section_end = j
                break

        work_lines = lines[start+1:section_end]

        # Group lines into blocks per job
        job_blocks = []
        current_block = []
        for line in work_lines:
            if re.search(r"(19|20)\d{2}", line) and current_block:
                job_blocks.append(current_block)
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            job_blocks.append(current_block)

        parsed_experiences = []
        date_formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%Y", "%Y", "%b %Y", "%B %Y"]

        for block in job_blocks:
            title = company = location = description = ""
            from_date = to_date = None
            block_text = " ".join(block)

            # Dates
            date_match = re.findall(
                r'(\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|\b\d{4})',
                block_text, re.IGNORECASE
            )
            if len(date_match) >= 1:
                from_date_str = date_match[0]
                for fmt in date_formats:
                    try:
                        from_date = datetime.strptime(from_date_str, fmt).date()
                        break
                    except:
                        pass
            if len(date_match) >= 2:
                to_date_str = date_match[1]
                if re.search(r'present', to_date_str, re.IGNORECASE):
                    to_date = date.today()
                else:
                    for fmt in date_formats:
                        try:
                            to_date = datetime.strptime(to_date_str, fmt).date()
                            break
                        except:
                            pass

            if not from_date:
                from_date = date(2000, 1, 1)
            if not to_date:
                to_date = date.today()

            # Assign block lines
            if block:
                title = block[0]
            if len(block) > 1:
                company = block[1]
            if len(block) > 2:
                location = block[2]
            if len(block) > 3:
                description = " ".join(block[3:])

            parsed_experiences.append({
                "title": title[:140],
                "company": company[:140],
                "location": location,
                "description": description,
                "current": 1 if not to_date or to_date == date.today() else 0,
                "from_date": from_date,
                "to_date": to_date
            })

        return parsed_experiences
