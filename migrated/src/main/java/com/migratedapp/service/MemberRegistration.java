package com.migratedapp.service;

import com.migratedapp.model.Member; // Assuming Member is translated to this package
import com.migratedapp.repository.MemberRepository; // Assuming a Spring Data MongoDB repository exists
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional; // Optional: Add if specific transactional behavior is needed beyond repository methods

/**
 * Service for registering new members.
 * Migrated from an EJB Stateless Session Bean {@code MemberRegistration}.
 * <p>
 * This service now uses Spring Data MongoDB for persistence via {@link MemberRepository}
 * and Spring's {@link ApplicationEventPublisher} for event handling.
 * </p>
 *
 * @see Member
 * @see MemberRepository
 * @see ApplicationEventPublisher
 */
@Service
public class MemberRegistration {

    private static final Logger log = LoggerFactory.getLogger(MemberRegistration.class);

    private final MemberRepository memberRepository;
    private final ApplicationEventPublisher eventPublisher;

    /**
     * Constructor-based dependency injection.
     *
     * @param memberRepository The repository for Member data access.
     * @param eventPublisher The Spring application event publisher.
     */
    @Autowired
    public MemberRegistration(MemberRepository memberRepository, ApplicationEventPublisher eventPublisher) {
        this.memberRepository = memberRepository;
        this.eventPublisher = eventPublisher;
    }

    /**
     * Registers a new member by persisting it to the database and publishing an event.
     * <p>
     * Replaces the EJB {@code EntityManager.persist} with Spring Data's {@code MongoRepository.save}
     * and CDI {@code Event.fire} with Spring's {@code ApplicationEventPublisher.publishEvent}.
     * </p>
     * <p>
     * Note: The original method declared {@code throws Exception}. Consider using more specific
     * exceptions or leveraging Spring's exception translation mechanisms if needed.
     * The {@code @Transactional} annotation can be added if multiple repository calls
     * need to be part of a single transaction, although basic save operations are often
     * transactional by default with Spring Data Repositories.
     * </p>
     *
     * @param member The member entity to register. Assumed to be a Spring Data MongoDB @Document.
     * @throws Exception Rethrows exceptions from the underlying operations (consider refinement).
     */
    // @Transactional // Uncomment if complex transactional behavior spanning multiple operations is required
    public void register(Member member) throws Exception {
        log.info("Registering {}", member.getName()); // Use SLF4j parameter binding
        // Persist the member using Spring Data MongoDB repository
        Member savedMember = memberRepository.save(member);
        log.info("Registered member with ID: {}", savedMember.getId()); // Assuming Member has getId() after save

        // Publish an event (e.g., for other components to react to the registration)
        // The published object is the saved member instance. Listeners can be created
        // using @EventListener annotation in other Spring components.
        eventPublisher.publishEvent(savedMember);
    }
}
