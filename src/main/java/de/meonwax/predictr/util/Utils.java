package de.meonwax.predictr.util;

import javax.servlet.http.HttpServletRequest;

public abstract class Utils {

    /**
     * Get the base URL to this application for use in external requests (e.g. mails)
     */
    public static String getBaseUrl(HttpServletRequest request) {
        String port = Integer.toString(request.getServerPort());
        port = port.equals("443") || port.equals("80") ? "" : ":" + port;
        return request.getScheme() + "://" + request.getServerName() + port;
    }
}
