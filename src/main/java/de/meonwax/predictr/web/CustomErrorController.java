package de.meonwax.predictr.web;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

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

    private final static Map<HttpStatus, String> myMap;
    static {
        Map<HttpStatus, String> m = new HashMap<>();
        m.put(HttpStatus.UNAUTHORIZED, "401.html");
        m.put(HttpStatus.NOT_FOUND, "404.html");
        m.put(HttpStatus.INTERNAL_SERVER_ERROR, "500.html");
        myMap = Collections.unmodifiableMap(m);
    }

    @Override
    public String getErrorPath() {
        return "error";
    }

    @RequestMapping(produces = MediaType.TEXT_HTML_VALUE)
    public String errorHtml(HttpServletRequest request) {
        String template = myMap.get(getStatus(request));
        if (template != null) {
            return template;
        }
        return "500.html";
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
}
