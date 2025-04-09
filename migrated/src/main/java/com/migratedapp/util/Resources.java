package com.migratedapp.util;

import org.springframework.context.annotation.Configuration;

/**
 * Placeholder class for original 'Resources.java' from the JBoss EAP Quickstart.
 *
 * The original class 'org.jboss.as.quickstarts.kitchensink.util.Resources' served as a CDI producer
 * for Jakarta EE resources like the JPA EntityManager and context-aware Loggers using {@code @Produces}.
 *
 * In this Spring Boot application using MongoDB, these specific producers are handled differently
 * or are not directly applicable:
 *
 * 1.  <p><b>EntityManager Producer (@Produces @PersistenceContext EntityManager):</b></p>
 *     This is specific to JPA and relational databases. For MongoDB, Spring Boot auto-configures
 *     beans like {@code MongoTemplate} or Spring Data Repositories when the
 *     {@code spring-boot-starter-data-mongodb} dependency is present. Components requiring
 *     database interaction should inject {@code MongoTemplate} or custom repository interfaces instead.
 *     There is no direct translation for producing a JPA EntityManager in a MongoDB context.
 *
 * 2.  <p><b>Logger Producer (@Produces Logger):</b></p>
 *     The original method provided a {@code java.util.logging.Logger} based on the injection point.
 *     The standard practice in Spring Boot is to use SLF4J (e.g., with Logback or Log4j2)
 *     and obtain loggers directly within the class:
 *     <pre>{@code
 *     import org.slf4j.Logger;
 *     import org.slf4j.LoggerFactory;
 *
 *     // Inside your class:
 *     private static final Logger log = LoggerFactory.getLogger(YourClassName.class);
 *     }</pre>
 *     Spring Boot's logging starter handles the underlying configuration. A custom producer bean
 *     for loggers is generally not needed or idiomatic in Spring.
 *
 * <p><b>Action Required:</b></p>
 * Review components in the original application that injected dependencies produced by this
 * {@code Resources} class. Update them to use the standard Spring Boot mechanisms:
 * <ul>
 *     <li>Inject {@code MongoTemplate} or Spring Data MongoDB Repositories for database access.</li>
 *     <li>Use {@code LoggerFactory.getLogger(...)} for logging.</li>
 * </ul>
 *
 * This class is retained as a placeholder and explanation during migration. It can likely be
 * removed after verifying that all dependent components have been updated. Adding {@code @Configuration}
 * allows Spring to scan it, but it defines no beans.
 *
 */
@Configuration // Mark as configuration, though it defines no beans currently.
public class Resources {

    // Content intentionally left empty as the original producer methods
    // are replaced by Spring Boot auto-configuration or standard practices.
    // See class Javadoc for details.

}
