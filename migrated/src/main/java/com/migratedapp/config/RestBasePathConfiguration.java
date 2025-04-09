package com.migratedapp.config;

import org.springframework.context.annotation.Configuration;

/**
 * Configuration class indicating how the JAX-RS base path is handled in Spring Boot.
 *
 * <p>The original source class {@code org.jboss.as.quickstarts.kitchensink.rest.JaxRsActivator}
 * extended {@code jakarta.ws.rs.core.Application} and used the {@code @ApplicationPath("/rest")}
 * annotation to define the base URI for all JAX-RS resources in the Jakarta EE application.
 * </p>
 *
 * <p>In Spring Boot, this explicit JAX-RS activation class is not required. The base path
 * for REST endpoints (corresponding to the original {@code "/rest"}) can be configured
 * in one of the following ways:
 * </p>
 * <ol>
 *   <li><b>Using application properties:</b> Set the application's context path in
 *      {@code src/main/resources/application.properties} or {@code application.yml}:
 *      <pre>server.servlet.context-path=/rest</pre>
 *      This affects the entire application context.
 *   </li>
 *   <li><b>Using Controller-level Mappings:</b> Define a base path directly on your
 *      Spring MVC or WebFlux controllers using {@code @RequestMapping("/rest")} at the
 *      class level. This is often preferred if only a subset of endpoints should share
 *      this prefix.
 *      <pre>
 *      import org.springframework.web.bind.annotation.RequestMapping;
 *      import org.springframework.web.bind.annotation.RestController;
 *
 *      {@literal @}RestController
 *      {@literal @}RequestMapping("/rest")
 *      public class MyRestController {
 *          // ... handler methods mapped relative to /rest
 *      }
 *      </pre>
 *   </li>
 * </ol>
 *
 * <p>This class serves as a marker and documentation point during migration. It does not
 * contain active configuration beans unless specific programmatic configuration related
 * to web paths is needed, which is uncommon for simple base path setting. Ensure your
 * REST controllers (e.g., migrated JAX-RS resources, now likely {@code @RestController} classes)
 * are correctly mapped according to the chosen approach.
 * </p>
 *
 * @see org.springframework.web.bind.annotation.RestController
 * @see org.springframework.web.bind.annotation.RequestMapping
 */
@Configuration
public class RestBasePathConfiguration {

    // This class body is intentionally left blank.
    // Its purpose is informational, guiding how the equivalent functionality
    // of the original JaxRsActivator is achieved in Spring Boot.
    // No beans are defined here as base path configuration is typically
    // handled declaratively (properties or annotations).

}
