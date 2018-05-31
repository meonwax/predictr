package de.meonwax.predictr.validator;

import org.springframework.stereotype.Component;
import org.springframework.validation.Errors;
import org.springframework.validation.Validator;

@Component
public class AvatarValidator implements Validator {

    private final static int UPLOAD_MAX_SIZE = 200 * 1024;
    public final static String[] ALLOWED_MIME_TYPES = new String[]{"image/png", "image/jpeg"};

    @Override
    public boolean supports(Class<?> clazz) {
        return clazz.isAssignableFrom(byte[].class);
    }

    @Override
    public void validate(Object target, Errors errors) {
        byte[] data = (byte[]) target;
        if (data.length > UPLOAD_MAX_SIZE) {
            errors.reject("max_size_exceed");
        }
    }
}
