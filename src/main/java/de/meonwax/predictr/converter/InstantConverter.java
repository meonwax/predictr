package de.meonwax.predictr.converter;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;
import java.sql.Timestamp;
import java.time.Instant;

@Converter(autoApply = true)
public class InstantConverter implements AttributeConverter<Instant, Timestamp> {

    @Override
    public java.sql.Timestamp convertToDatabaseColumn(Instant entityValue) {
        if (entityValue == null) {
            return null;
        }
        return Timestamp.from(entityValue);
    }

    @Override
    public Instant convertToEntityAttribute(Timestamp databaseValue) {
        if (databaseValue == null) {
            return null;
        }
        return databaseValue.toInstant();
    }
}
