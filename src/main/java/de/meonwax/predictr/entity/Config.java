package de.meonwax.predictr.entity;

import io.micronaut.core.annotation.Nullable;
import io.micronaut.data.annotation.Id;
import io.micronaut.data.annotation.MappedEntity;
import io.micronaut.serde.annotation.Serdeable;

@MappedEntity
@Serdeable
public record Config(
    @Id Long id,
    String title,
    String owner,
    String adminEmail,
    Boolean showImportantMessage,
    Integer pointsResult,
    Integer pointsTendency,
    Integer pointsTendencySpread,
    @Nullable String rulesEn,
    @Nullable String rulesDe
) {
}
