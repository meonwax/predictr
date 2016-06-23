package de.meonwax.predictr.web;

import java.io.IOException;
import java.util.Arrays;

import javax.validation.Valid;
import javax.validation.constraints.NotNull;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.WebDataBinder;
import org.springframework.web.bind.annotation.InitBinder;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;

import de.meonwax.predictr.domain.Avatar;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.service.AvatarService;
import de.meonwax.predictr.validator.AvatarValidator;

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
    public ResponseEntity<byte[]> getAvatar(@PathVariable Long userId) throws IOException {
        Avatar avatar = avatarService.getAvatar(userId);
        if (avatar != null) {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.valueOf(avatar.getMimeType()));
            return ResponseEntity.ok().headers(headers).body(avatar.getData());
        }
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(null);
    }

    @RequestMapping(value = "/users/avatar", method = RequestMethod.POST, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Void> uploadAvatar(
            @NotNull @RequestHeader(value = HttpHeaders.CONTENT_TYPE) MediaType contentType,
            @Valid @RequestBody byte[] avatarData,
            BindingResult result,
            @AuthenticationPrincipal User user) throws IOException {
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
    public ResponseEntity<Void> deleteAvatar(@AuthenticationPrincipal User user) throws IOException {
        avatarService.deleteAvatar(user);
        return ResponseEntity.ok().build();
    }
}
