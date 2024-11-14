/** @odoo-module **/

import { session } from '@web/session'; 
import { registry } from '@web/core/registry';
import { browser } from '@web/core/browser/browser';

// This function is triggered after the page is loaded
document.addEventListener('DOMContentLoaded', function () {
    if (session) {
        // Once the user is logged in, attempt to auto-select companies if available
        autoSelectAllowedCompanies();
    }
});

// Function to auto-select allowed companies based on session data
function autoSelectAllowedCompanies() {
    const allowedCompanies = session.user_companies.allowed_companies;

    // Check if allowed companies exist
    if (!allowedCompanies || Object.keys(allowedCompanies).length === 0) {
        console.error("No allowed companies found in session.");
        return;
    }

    console.log('Allowed Companies:', allowedCompanies);

    // Extract company IDs from the session data (assuming they are numeric)
    const allowedCompanyIds = Object.keys(allowedCompanies).map(Number);

    // If there are multiple allowed companies, automatically select them
    if (allowedCompanyIds.length > 1) {
        updateActiveCompanyContext(allowedCompanyIds);
    }
}

// Function to update the user context with the allowed companies
function updateActiveCompanyContext(companyIds) {
    const { user_companies } = session;

    // We can set the active companies here, ensuring that we don't select disallowed ones.
    const activeCompanyIds = computeActiveCompanyIds(companyIds);

    // Update the user context with the selected companies
    // Assuming there's a method in Odoo 18 that allows us to update the company context
    session.user_companies.active_company_ids = activeCompanyIds;

    console.log(`Selected Companies: ${activeCompanyIds}`);

    // // Trigger a reload if necessary to reflect the changes in the UI
    // browser.setTimeout(() => {
    //     browser.location.reload(); // This forces a page reload to reflect the new company context
    // });
}

// Computes active company IDs based on session and allowed companies
function computeActiveCompanyIds(companyIds) {
    const { user_companies } = session;
    let activeCompanyIds = companyIds || [];
    const availableCompaniesFromSession = user_companies.allowed_companies;
    const notAllowedCompanies = activeCompanyIds.filter(
        (id) => !(id in availableCompaniesFromSession)
    );

    // If no companies are selected or selected companies are not allowed, fall back to the current company
    if (!activeCompanyIds.length || notAllowedCompanies.length) {
        activeCompanyIds = [user_companies.current_company];
    }

    if (session.is_login) {
        // If the user is logged in, select all allowed companies
        activeCompanyIds = Object.keys(availableCompaniesFromSession).map(Number);
    }

    return activeCompanyIds;
}
