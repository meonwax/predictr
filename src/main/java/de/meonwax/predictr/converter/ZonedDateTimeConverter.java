package de.meonwax.predictr.converter;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;

import javax.persistence.AttributeConverter;
import javax.persistence.Converter;

@Converter(autoApply = true)
public class ZonedDateTimeConverter implements AttributeConverter<ZonedDateTime, Timestamp> {

	@Override
	public java.sql.Timestamp convertToDatabaseColumn(ZonedDateTime entityValue) {
		return Timestamp.from(entityValue.toInstant());
	}

	@Override
	public ZonedDateTime convertToEntityAttribute(Timestamp databaseValue) {
		LocalDateTime localDateTime = databaseValue.toLocalDateTime();
		return localDateTime.atZone(ZoneId.systemDefault());
	}
}