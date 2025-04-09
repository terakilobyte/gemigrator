/*
 * Translated default_api from JAX-RS to Spring Boot.
 * Original file: src/main/java/org/jboss/as/quickstarts/kitchensink/rest/MemberResourceRESTService.java
 */
package com.migratedapp.controller;

import com.migratedapp.model.Member;
import com.migratedapp.service.MemberService; // Assuming MemberRegistration is translated to MemberService
import com.migratedapp.exception.ResourceNotFoundException; // Custom exception for handling not found scenarios
import com.migratedapp.exception.DuplicateEmailException; // Custom exception for handling email conflicts

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import jakarta.validation.Valid; // Replaces manual validation trigger for request body
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException; // Alternative for simple error responses

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * Spring Boot REST Controller equivalent of the JAX-RS MemberResourceRESTService.
 * Handles HTTP requests related to Member resources.
 *
 * Assumes:
 * - Member class is updated to be a Spring Data MongoDB @Document with a String ID.
 * - MemberRepository is updated to be a Spring Data MongoRepository interface.
 * - MemberRegistration service is translated to MemberService (@Service).
 * - Custom exceptions like ResourceNotFoundException and DuplicateEmailException are defined.
 * - Global exception handling (@ControllerAdvice) might be used for cleaner error handling,
 *   but local @ExceptionHandler is shown here for direct translation illustration.
 */
@RestController
@RequestMapping("/api/members") // Base path for member related endpoints (added /api prefix)
public class MemberController {

    // Use SLF4j for logging, standard in Spring Boot
    private static final Logger log = LoggerFactory.getLogger(MemberController.class);

    private final MemberService memberService;

    /**
     * Constructor injection is preferred in Spring.
     * @param memberService The service handling member business logic.
     */
    @Autowired
    public MemberController(MemberService memberService) {
        this.memberService = memberService;
        // Validator is typically not needed directly in the controller when using @Valid
    }

    /**
     * Retrieves all members, ordered by name.
     * Corresponds to the original listAllMembers method.
     * @return List of all members.
     */
    @GetMapping(produces = MediaType.APPLICATION_JSON_VALUE)
    public List<Member> listAllMembers() {
        log.info("Received request to list all members");
        return memberService.findAllOrderedByName();
    }

    /**
     * Retrieves a specific member by their ID.
     * Corresponds to the original lookupMemberById method.
     * Assumes Member ID is now String for MongoDB.
     * @param id The ID of the member to retrieve.
     * @return The found Member.
     * @throws ResourceNotFoundException if no member with the given ID exists.
     */
    @GetMapping(path = "/{id}", produces = MediaType.APPLICATION_JSON_VALUE)
    public Member lookupMemberById(@PathVariable("id") String id) {
        log.info("Received request to lookup member by id: {}", id);
        return memberService.findById(id)
                .orElseThrow(() -> {
                    log.warn("Member with id {} not found", id);
                    // Throwing custom exception, typically handled by @ControllerAdvice
                    // Or use Spring's ResponseStatusException for simpler cases:
                    // throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found");
                    return new ResourceNotFoundException("Member not found with id: " + id);
                });
    }

    /**
     * Creates a new member from the provided data.
     * Performs validation using @Valid.
     * Corresponds to the original createMember method.
     * @param member The member data from the request body.
     * @return ResponseEntity indicating success (201 Created) or failure (400 Bad Request, 409 Conflict).
     */
    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<?> createMember(@Valid @RequestBody Member member) {
        // @Valid triggers Bean Validation automatically. ConstraintViolationException will be thrown if invalid.
        log.info("Received request to create member: {}", member.getEmail());
        try {
            Member registeredMember = memberService.register(member);
            // Return 201 Created status with the created member or its location
            return ResponseEntity.status(HttpStatus.CREATED).body(registeredMember);
        } catch (DuplicateEmailException e) {
            log.warn("Failed to create member, email already exists: {}", member.getEmail());
            Map<String, String> responseObj = new HashMap<>();
            responseObj.put("email", e.getMessage()); // Use message from custom exception
            return ResponseEntity.status(HttpStatus.CONFLICT).body(responseObj);
        }
        // ConstraintViolationException and other potential exceptions can be handled by @ExceptionHandler methods
        // or a global @ControllerAdvice. A generic handler is omitted here for brevity,
        // assuming a global handler or specific handlers below cover the main cases.
    }

    /**
     * Handles Bean Validation constraint violations.
     * Creates a response similar to the original createViolationResponse method.
     * This can be moved to a @ControllerAdvice for global handling.
     * @param ex The exception containing violation details.
     * @return ResponseEntity with status 400 (Bad Request) and validation errors.
     */
    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, String> handleConstraintViolation(ConstraintViolationException ex) {
        Set<ConstraintViolation<?>> violations = ex.getConstraintViolations();
        log.warn("Validation failed. Violations found: {}", violations.size());

        Map<String, String> errors = new HashMap<>();
        for (ConstraintViolation<?> violation : violations) {
            // Get the field name (property path) and the error message
            String fieldName = violation.getPropertyPath().toString();
            String message = violation.getMessage();
            errors.put(fieldName, message);
            log.debug("Validation error - Field: '{}', Message: '{}'", fieldName, message);
        }
        return errors;
    }

     /**
      * Handles ResourceNotFoundException.
      * This can be moved to a @ControllerAdvice for global handling.
      * @param ex The exception.
      * @return ResponseEntity with status 404 (Not Found).
      */
     @ExceptionHandler(ResourceNotFoundException.class)
     @ResponseStatus(HttpStatus.NOT_FOUND)
     public Map<String, String> handleResourceNotFound(ResourceNotFoundException ex) {
         Map<String, String> responseObj = new HashMap<>();
         responseObj.put("error", ex.getMessage());
         return responseObj;
     }

    // Note: The original validateMember and emailAlreadyExists logic is now expected
    // to reside within the MemberService.register() method.
    // The @Valid annotation handles the basic bean validation part.
    // The email uniqueness check should be performed by the service before saving.
}
