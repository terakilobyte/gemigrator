package com.migratedapp.repository;

import com.migratedapp.model.Member;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository interface for managing {@link Member} documents in MongoDB.
 * 
 * Original Source Analysis:
 * The source class 'org.jboss.as.quickstarts.kitchensink.data.MemberRepository' was identified as a
 * JPA Repository/DAO class. It used Jakarta EE's @ApplicationScoped and @Inject annotations
 * along with the Jakarta Persistence API (EntityManager, Criteria API) to perform database operations.
 *
 * Translation Notes:
 * - This interface replaces the original class-based repository.
 * - It extends Spring Data MongoDB's {@link MongoRepository}, which provides standard CRUD operations
 *   (like findById, save, delete) out-the-box, replacing the need for an EntityManager implementation.
 * - The {@code findById} method is implicitly provided by MongoRepository.
 * - The custom query methods {@code findByEmail} and {@code findAllOrderedByName} from the original
 *   class have been translated into Spring Data query methods. Spring Data automatically derives
 *   the MongoDB queries from the method names.
 * - {@code findByEmail} now returns an {@link Optional<Member>} which is more idiomatic in Spring Data
 *   than the original JPA {@code getSingleResult()} which would throw an exception if not found.
 *   The calling service layer should handle the Optional accordingly.
 * - {@code findAllOrderedByName} is translated to {@code findAllByOrderByNameAsc}.
 * - The {@code Member} class referenced here is assumed to be translated into a Spring Data MongoDB
 *   {@code @Document} class in the {@code com.migratedapp.model} package.
 * - The ID type for Member is assumed to be {@link Long}. If MongoDB ObjectIds (String) are used,
 *   the signature should be changed to {@code MongoRepository<Member, String>}.
 * - No explicit @Repository annotation is strictly necessary when extending MongoRepository if component scanning
 *   is configured correctly, but it can be added for clarity.
 */
@Repository // Optional, but good practice for clarity
public interface MemberRepository extends MongoRepository<Member, Long> {

    /**
     * Finds a Member document by its email address.
     * Corresponds to the original {@code findByEmail} method using Criteria API.
     *
     * @param email The email address to search for.
     * @return An Optional containing the found Member, or Optional.empty() if not found.
     */
    Optional<Member> findByEmail(String email);

    /**
     * Finds all Member documents and orders them by name in ascending order.
     * Corresponds to the original {@code findAllOrderedByName} method using Criteria API.
     *
     * @return A List of Member documents ordered by name.
     */
    List<Member> findAllByOrderByNameAsc();

}
