package de.meonwax.util;

public abstract class Utils {

    /**
     * Checks if all objects in the array are not {@code null}s.
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
}
