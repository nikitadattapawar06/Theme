frappe.ui.form.on("Resume Upload", {
    refresh(frm) {
        frm.add_custom_button("Parse Resume", () => {
            frappe.call({
                method: "parse_resumes",
                doc: frm.doc,
                freeze: true,
                freeze_message: "Parsing resume and creating Job Applicant...",
                callback: function(r) {
                    if (!r.exc && r.message) {
                        frappe.msgprint({
                            title: "Success",
                            indicator: "green",
                            message: `✅ Job Applicant created: 
                                <a href="/app/job-applicant/${r.message}" target="_blank">${r.message}</a>`
                        });
                        frm.reload_doc();
                    } else {
                        frappe.msgprint("Resume parsed, but Job Applicant creation failed.");
                    }
                }
            });
        });
    }
});
