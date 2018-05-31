package de.meonwax.predictr.dto;

import de.meonwax.predictr.domain.User;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RankDto {

    private User user;

    private Integer points;

    private Integer position;
}
