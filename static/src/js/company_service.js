/** @odoo-module **/

import { companyService as companyServiceBase } from "@web/webclient/company_service";
import { cookie } from "@web/core/browser/cookie";
import { user } from "@web/core/user";
import { router } from "@web/core/browser/router";
import { session } from "@web/session";


const CIDS_HASH_SEPARATOR = "-";

function parseCompanyIds(cids, separator = CIDS_HASH_SEPARATOR) {
    if (typeof cids === "string") {
        return cids.split(separator).map(Number);
    } else if (typeof cids === "number") {
        return [cids];
    }
    return [];
}

function computeActiveCompanyIds(cids) {
    const { user_companies } = session;
    let activeCompanyIds = cids || Object.keys(user_companies.allowed_companies).map(Number);

    const availableCompaniesFromSession = user_companies.allowed_companies;
    const notAllowedCompanies = activeCompanyIds.filter(
        (id) => !(id in availableCompaniesFromSession)
    );

    if (!activeCompanyIds.length || notAllowedCompanies.length) {
        activeCompanyIds = [user_companies.current_company];
    }

    if (session.is_login){
        activeCompanyIds = Object.keys(availableCompaniesFromSession).map(Number);
    }
    return activeCompanyIds;
}

function getCompanyIds() {
    let cids;
    const state = router.current;
    if ("cids" in state) {
        if (typeof state.cids === "string" && !state.cids.includes(CIDS_HASH_SEPARATOR)) {
            cids = parseCompanyIds(state.cids, ",");
        } else {
            cids = parseCompanyIds(state.cids);
        }
    } else if (cookie.get("cids")) {
        cids = parseCompanyIds(cookie.get("cids"));
    }
    return cids || [];
}

const originalStart = companyServiceBase.start;
companyServiceBase.start = function(env, { action, orm }) {
    const allowedCompanies = session.user_companies.allowed_companies;
    const disallowedAncestorCompanies = session.user_companies.disallowed_ancestor_companies;
    const allowedCompaniesWithAncestors = {
        ...allowedCompanies,
        ...disallowedAncestorCompanies,
    };
    const activeCompanyIds = computeActiveCompanyIds(getCompanyIds());

    cookie.set("cids", activeCompanyIds.join(CIDS_HASH_SEPARATOR));
    user.updateContext({ allowed_company_ids: activeCompanyIds });

    return {
        allowedCompanies,
        allowedCompaniesWithAncestors,
        disallowedAncestorCompanies,

        get activeCompanyIds() {
            return activeCompanyIds.slice();
        },

        get currentCompany() {
            return allowedCompanies[activeCompanyIds[0]];
        },

        getCompany(companyId) {
            return allowedCompaniesWithAncestors[companyId];
        },

        async setCompanies(companyIds, includeChildCompanies = true) {
            const newCompanyIds = companyIds.length ? companyIds : Object.keys(allowedCompanies).map(Number);

            function addCompanies(companyIds) {
                for (const companyId of companyIds) {
                    if (!newCompanyIds.includes(companyId)) {
                        newCompanyIds.push(companyId);
                        addCompanies(allowedCompanies[companyId].child_ids);
                    }
                }
            }

            if (includeChildCompanies) {
                addCompanies(
                    companyIds.flatMap((companyId) => allowedCompanies[companyId].child_ids)
                );
            }

            cookie.set("cids", newCompanyIds.join(CIDS_HASH_SEPARATOR));
            user.updateContext({ allowed_company_ids: newCompanyIds });

            const controller = action.currentController;
            const state = {};
            const options = { reload: true };
            if (controller?.props.resId && controller?.props.resModel) {
                const hasReadRights = await user.checkAccessRight(
                    controller.props.resModel,
                    "read",
                    controller.props.resId
                );

                if (!hasReadRights) {
                    options.replace = true;
                    state.actionStack = router.current.actionStack.slice(0, -1);
                }
            }
            router.pushState(state, options);
        },
    };
};
