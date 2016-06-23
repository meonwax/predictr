package de.meonwax.predictr.web;

import java.io.PrintWriter;
import java.io.StringWriter;
import java.time.ZonedDateTime;

import javax.servlet.http.HttpServletRequest;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.web.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RequestMapping;

import de.meonwax.predictr.service.MailService;
import de.meonwax.predictr.settings.Settings;

@Controller
@RequestMapping("error")
public class CustomErrorController implements ErrorController {

    @Autowired
    private MailService mailService;

    @Autowired
    private Settings settings;

    @Override
    public String getErrorPath() {
        return "error";
    }

    @RequestMapping(produces = MediaType.TEXT_HTML_VALUE)
    @ExceptionHandler(NullPointerException.class)
    public String errorHtml(HttpServletRequest request) {
        return getTemplate(getStatus(request));
    }

    @RequestMapping
    public ResponseEntity<Void> error(HttpServletRequest request) {
        return ResponseEntity.status(getStatus(request)).build();
    }

    private HttpStatus getStatus(HttpServletRequest request) {
        Integer statusCode = (Integer) request.getAttribute("javax.servlet.error.status_code");
        if (mailService.isEnabled() && statusCode >= HttpStatus.INTERNAL_SERVER_ERROR.value()) {
            sendMail((Exception) request.getAttribute("javax.servlet.error.exception"));
        }
        if (statusCode != null) {
            try {
                return HttpStatus.valueOf(statusCode);
            } catch (IllegalArgumentException e) {
            }
        }
        return HttpStatus.INTERNAL_SERVER_ERROR;
    }

    private String getTemplate(HttpStatus status) {
        return "templates/" + status.value() + ".html";
    }

    private void sendMail(Exception e) {

        String exceptionDump = "";
        String exceptionName = "Unknown exception";

        // Gather exception details
        if (e != null) {
            if (e.getCause() != null) {
                e = (Exception) e.getCause();
            }
            StringWriter stringWriter = new StringWriter();
            e.printStackTrace(new PrintWriter(stringWriter));
            exceptionDump = stringWriter.toString();
            exceptionName = e.getClass().getSimpleName();
        }

        // Construct mail
        String receipent = settings.getAdminEmail();
        String subject = settings.getTitle() + ": " + exceptionName + " thrown";
        String text = ZonedDateTime.now() + "\n\n" + exceptionDump;

        mailService.send(receipent, subject, text);
    }
}
