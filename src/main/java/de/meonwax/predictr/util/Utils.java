package de.meonwax.predictr.util;

import java.io.IOException;

import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.core.JsonParseException;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonMappingException;
import com.fasterxml.jackson.databind.ObjectMapper;

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
        } catch (JsonParseException e) {
            e.printStackTrace();
        } catch (JsonMappingException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }
}
