frappe.form.link_formatters['Employee'] = function(value, doc) {
    if(doc.employee_name && doc.employee_name !== value) {
        return value + ': ' + doc.employee_name;
    } else {
        return value;
    }
}
/*
frappe.form.link_formatters['Item'] = function(value, doc) {
    if (doc.doctype != "Batch"){
    if(doc.item_name && doc.item_name !== value) {
        return value + ': ' + doc.item_name;
    } else {
        return value;
    }
    }
}
*/