package de.meonwax.predictr.exception;

public class PasswordResetException extends Exception {

    private static final long serialVersionUID = 1L;

    public PasswordResetException(String message) {
        super(message);
    }
}
