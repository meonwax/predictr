package de.meonwax.predictr.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.stereotype.Service;

import de.meonwax.predictr.settings.Settings;

@Service
public class MailService {

    private final Logger log = LoggerFactory.getLogger(MailService.class);

    @Autowired
    private JavaMailSenderImpl mailSender;

    @Value("${spring.mail.host}")
    private String mailHost;

    @Value("${spring.mail.tls}")
    private Boolean tls;

    @Autowired
    private Settings settings;

    public boolean isEnabled() {
        return mailHost != null && mailHost.length() > 0;
    }

    public boolean send(String recipient, String subject, String text) {
        if (tls) {
            mailSender.getJavaMailProperties().setProperty("mail.smtp.starttls.enable", "true");
        }
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(settings.getAdminEmail());
        message.setTo(recipient);
        message.setSubject(subject);
        message.setText(text);
        try {
            mailSender.send(message);
        } catch (MailException e) {
            log.error("Error sending mail: " + e.getMessage());
            return false;
        }
        return true;
    }
}
