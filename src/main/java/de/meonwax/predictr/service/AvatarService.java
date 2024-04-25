package de.meonwax.predictr.service;

import de.meonwax.predictr.domain.Avatar;
import de.meonwax.predictr.domain.User;
import de.meonwax.predictr.repository.AvatarRepository;
import de.meonwax.predictr.repository.UserRepository;
import lombok.AllArgsConstructor;
import org.imgscalr.Scalr;
import org.imgscalr.Scalr.Method;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.Objects;
import java.util.Optional;

@Service
@AllArgsConstructor
public class AvatarService {

    private static final Logger LOGGER = LoggerFactory.getLogger(AvatarService.class);

    private final static int AVATAR_WIDTH = 64;
    private final static int AVATAR_HEIGHT = 64;

    private final static int IMAGE_RESIZE_DIMENSION = 128;

    private final static String FONT_FILE = "Lato-Black.ttf";
    private final static float FONT_RATIO = .7f;

    // Predefined colors inspired by https://github.com/judesfernando/initial.js
    private final static Color[] COLORS = new Color[]{
        new Color(0x1abc9c),
        new Color(0x16a085),
        new Color(0xf1c40f),
        new Color(0xf39c12),
        new Color(0x2ecc71),
        new Color(0x27ae60),
        new Color(0xe67e22),
        new Color(0xd35400),
        new Color(0x3498db),
        new Color(0x2980b9),
        new Color(0xe74c3c),
        new Color(0xc0392b),
        new Color(0x9b59b6),
        new Color(0x8e44ad),
        new Color(0xbdc3c7),
        new Color(0x34495e),
        new Color(0x2c3e50),
        new Color(0x95a5a6),
        new Color(0x7f8c8d),
        new Color(0xec87bf),
        new Color(0xd870ad),
        new Color(0xf69785),
        new Color(0x9ba37e),
        new Color(0xb49255),
        new Color(0xb49255),
        new Color(0xa94136)
    };

    private final AvatarRepository avatarRepository;

    private final UserRepository userRepository;

    public Optional<Avatar> getAvatar(Long userId) {
        return userRepository.findById(userId)
            .map(user -> {
                Avatar avatar = user.getAvatar();
                if (avatar == null) {
                    avatar = generateGenericAvatar(user);
                }
                return Optional.of(avatar);
            })
            .orElse(Optional.empty());
    }

    public void setAvatar(User user, byte[] data, MediaType contentType) {
        data = resizeAvatar(data, contentType);

        Avatar avatar = user.getAvatar();
        if (avatar == null) {
            avatar = new Avatar();
        }
        avatar.setMimeType(contentType.getType() + "/" + contentType.getSubtype());
        avatar.setData(data);
        avatarRepository.save(avatar);

        user.setAvatar(avatar);
        userRepository.save(user);
    }

    public void deleteAvatar(User user) {
        Avatar avatar = user.getAvatar();
        if (avatar != null) {
            user.setAvatar(null);
            userRepository.save(user);
            avatarRepository.delete(avatar);
        }
    }

    private Avatar generateGenericAvatar(User user) {

        // User's initial character
        char initial = user.getName().toUpperCase().charAt(0);

        // Create image
        BufferedImage image = new BufferedImage(AVATAR_WIDTH, AVATAR_HEIGHT, BufferedImage.TYPE_3BYTE_BGR);
        Graphics2D g = image.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        try (InputStream is = new BufferedInputStream(Objects.requireNonNull(getClass().getClassLoader().getResourceAsStream(FONT_FILE)))) {
            // Set font
            Font font = Font.createFont(Font.TRUETYPE_FONT, is);
            g.setFont(font.deriveFont(Font.PLAIN, FONT_RATIO * AVATAR_HEIGHT));

            // Set colors
            g.setColor(getBackgroundColor(initial));
            g.fillRect(0, 0, image.getWidth(), image.getHeight());
            g.setColor(Color.WHITE);

            // Determine text dimensions
            int textWidth = g.getFontMetrics().stringWidth(String.valueOf(initial));
            int textHeight = g.getFontMetrics().getHeight();
            int textAscent = g.getFontMetrics().getAscent();

            // Actually draw the initial
            g.drawString(String.valueOf(initial), image.getWidth() / 2 - textWidth / 2, (image.getHeight() - textHeight) / 2 + textAscent);

            // Convert into PNG format
            ImageIO.write(image, "png", baos);
            g.dispose();
        } catch (IOException | FontFormatException e) {
            LOGGER.warn("Error creating avatar: {}", e.getMessage());
        }
        byte[] data = baos.toByteArray();

        // Create avatar response object
        Avatar avatar = new Avatar();
        avatar.setData(data);
        avatar.setMimeType(MediaType.IMAGE_PNG_VALUE);
        return avatar;
    }

    private Color getBackgroundColor(char initial) {
        int i = initial % COLORS.length;
        return COLORS[i];
    }

    private byte[] resizeAvatar(byte[] data, MediaType contentType) {
        BufferedImage image;
        try {
            // Convert to image
            image = ImageIO.read(new ByteArrayInputStream(data));

            // Scale to dimension bounds maintaining aspect ratio
            if (image.getHeight() > IMAGE_RESIZE_DIMENSION || image.getWidth() > IMAGE_RESIZE_DIMENSION) {
                image = Scalr.resize(image, Method.ULTRA_QUALITY, IMAGE_RESIZE_DIMENSION);
            }

            int imgW = image.getWidth();
            int imgH = image.getHeight();

            // Pad to create square image
            if (imgW != imgH) {
                BufferedImage newImage = new BufferedImage(IMAGE_RESIZE_DIMENSION, IMAGE_RESIZE_DIMENSION, image.getType());
                Graphics g = newImage.getGraphics();
                g.setColor(Color.BLACK);
                g.fillRect(0, 0, newImage.getWidth(), newImage.getHeight());
                if (imgW > imgH) {
                    g.drawImage(image, 0, (IMAGE_RESIZE_DIMENSION - imgH) / 2, null);
                } else {
                    g.drawImage(image, (IMAGE_RESIZE_DIMENSION - imgW) / 2, 0, null);
                }
                g.dispose();

                image.flush();
                image = newImage;
            }

            // Convert back to byte array
            ByteArrayOutputStream baos = new ByteArrayOutputStream();
            ImageIO.write(image, contentType.getSubtype(), baos);
            image.flush();
            return baos.toByteArray();
        } catch (IOException e) {
            LOGGER.warn("Error resizing avatar: {}", e.getMessage());
        }
        return null;
    }
}
