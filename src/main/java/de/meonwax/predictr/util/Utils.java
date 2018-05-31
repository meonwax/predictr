package de.meonwax.predictr.util;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import javax.servlet.http.HttpServletRequest;
import java.io.IOException;

public abstract class Utils {

    /**
     * Check if all objects in the array are not {@code null}s.
     * If any object is {@code null} or the array is {@code null}, {@code false} is returned.
     * If all objects in array are not {@code null} or the array is empty (contains no elements), {@code true} is returned.
     */
    public static boolean allNotNull(final Object... objects) {
        if (objects == null) {
            return false;
        }
        for (final Object o : objects) {
            if (o == null) {
                return false;
            }
        }
        return true;
    }

    /**
     * Serialize any Java object to a String
     */
    public static String jsonSerialize(Object object, boolean ignoreNullFields) {
        ObjectMapper mapper = new ObjectMapper();
        if (ignoreNullFields) {
            mapper.setSerializationInclusion(Include.NON_NULL);
        }
        try {
            return mapper.writeValueAsString(object);
        } catch (JsonProcessingException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * Deserialize JSON content to a given result type
     */
    public static <T> T jsonDeserialize(String json, Class<T> type) {
        try {
            return new ObjectMapper().readValue(json, type);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }

    /**
     * Get the base URL to this application for use in external requests (e.g. mails)
     */
    public static String getBaseUrl(HttpServletRequest request) {
        String port = Integer.toString(request.getServerPort());
        port = port.equals("443") || port.equals("80") ? "" : ":" + port;
        return request.getScheme() + "://" + request.getServerName() + port;
    }
}
