package de.meonwax.predictr.web;

import javax.servlet.http.HttpServletRequest;

import org.springframework.boot.autoconfigure.web.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
@RequestMapping("error")
public class CustomErrorController implements ErrorController {

    @Override
    public String getErrorPath() {
        return "error";
    }

    @RequestMapping(produces = MediaType.TEXT_HTML_VALUE)
    public String errorHtml(HttpServletRequest request) {
        return getTemplate(getStatus(request));
    }

    @RequestMapping
    public ResponseEntity<Void> error(HttpServletRequest request) {
        return ResponseEntity.status(getStatus(request)).build();
    }

    private HttpStatus getStatus(HttpServletRequest request) {
        Integer statusCode = (Integer) request.getAttribute("javax.servlet.error.status_code");
        if (statusCode != null) {
            try {
                return HttpStatus.valueOf(statusCode);
            } catch (Exception e) {
            }
        }
        return HttpStatus.INTERNAL_SERVER_ERROR;
    }

    private String getTemplate(HttpStatus status) {
        return "templates/" + status.value() + ".html";
    }
}
