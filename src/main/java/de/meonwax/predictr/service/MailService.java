package de.meonwax.predictr.service;

import de.meonwax.predictr.settings.Settings;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.MailException;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSenderImpl;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Properties;

@Service
@RequiredArgsConstructor
public class MailService {

    private static final Logger LOGGER = LoggerFactory.getLogger(MailService.class);

    private final JavaMailSenderImpl mailSender;

    @Value("${spring.mail.host}")
    private String mailHost;

    @Value("${spring.mail.senderHost}")
    private String senderHost;

    @Value("${spring.mail.port}")
    private Integer port;

    @Value("${spring.mail.tls}")
    private Boolean tls;

    private final Settings settings;

    public boolean isEnabled() {
        return !StringUtils.isEmpty(mailHost);
    }

    public boolean send(String recipient, String subject, String text) {
        Properties properties = mailSender.getJavaMailProperties();
        properties.put("mail.smtp.socketFactory.port", port);
        if (port == 465) {
            properties.put("mail.smtp.socketFactory.class", "javax.net.ssl.SSLSocketFactory");
        }
        if (tls) {
            properties.setProperty("mail.smtp.starttls.enable", "true");
        }
        if (!StringUtils.isEmpty(senderHost)) {
            properties.setProperty("mail.smtp.localhost", senderHost);
        }
        SimpleMailMessage message = new SimpleMailMessage();
        message.setFrom(settings.getAdminEmail());
        message.setTo(recipient);
        message.setSubject(subject);
        message.setText(text);
        try {
            mailSender.send(message);
        } catch (MailException e) {
            LOGGER.error("Error sending mail: {}", e.getMessage());
            return false;
        }
        LOGGER.info("Mail '{}' sent to: {}", subject, recipient);
        return true;
    }
}
