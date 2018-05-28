package de.meonwax.predictr.web;

import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.service.AvatarService;
import de.meonwax.predictr.validator.AvatarValidator;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;
import java.util.Arrays;

@RestController
@RequestMapping("api")
public class AvatarController {

    @Autowired
    private AvatarService avatarService;

    @Autowired
    private AvatarValidator avatarValidator;

    @InitBinder
    protected void initAvatarBinder(WebDataBinder binder) {
        binder.setValidator(avatarValidator);
    }

    @RequestMapping(value = "/users/avatar/{userId}", method = RequestMethod.GET, produces = MediaType.IMAGE_JPEG_VALUE)
    public ResponseEntity<byte[]> getAvatar(@PathVariable Long userId) {
        return avatarService.getAvatar(userId)
            .map(avatar -> {
                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.valueOf(avatar.getMimeType()));
                return ResponseEntity.ok()
                    .headers(headers)
                    .body(avatar.getData());
            })
            .orElse(ResponseEntity.notFound().build());
    }

    @RequestMapping(value = "/users/avatar", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> uploadAvatar(
        @NotNull @RequestHeader(value = HttpHeaders.CONTENT_TYPE) MediaType contentType,
        @Valid @RequestBody byte[] avatarData,
        BindingResult result,
        @AuthenticationPrincipal User user) {
        if (!result.hasErrors()) {
            // Unfortunately, Spring doesn't support validation on @RequestHeader annotated params, so we have to do it manually.
            // See also: https://jira.spring.io/browse/SPR-6380
            String mimeType = contentType.getType() + "/" + contentType.getSubtype();
            if (Arrays.asList(AvatarValidator.ALLOWED_MIME_TYPES).contains(mimeType)) {
                avatarService.setAvatar(user, avatarData, contentType);
                return ResponseEntity.ok().build();
            }
        }
        return ResponseEntity.badRequest().build();
    }

    @RequestMapping(value = "/users/avatar", method = RequestMethod.DELETE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> deleteAvatar(@AuthenticationPrincipal User user) {
        avatarService.deleteAvatar(user);
        return ResponseEntity.ok().build();
    }
}
