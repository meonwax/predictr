package de.meonwax.predictr.repository;

import de.meonwax.predictr.entity.Config;
import io.micronaut.data.jdbc.annotation.JdbcRepository;
import io.micronaut.data.model.query.builder.sql.Dialect;
import io.micronaut.data.repository.CrudRepository;

@JdbcRepository(dialect = Dialect.POSTGRES)
public interface ConfigRepository extends CrudRepository<Config, Long> {
}
