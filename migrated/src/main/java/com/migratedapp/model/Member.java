package com.migratedapp.model;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import java.io.Serializable; // Kept from original, review if needed

/**
 * Represents a Member entity, migrated from JPA to Spring Data MongoDB.
 *
 * This class is annotated with {@link Document} to mark it as a MongoDB document,
 * stored in the "members" collection. The original {@code @Entity} and {@code @Table}
 * annotations have been replaced.
 *
 * The primary identifier {@code @Id} is mapped to MongoDB's {@code _id} field. The type
 * has been changed from Long to String to accommodate MongoDB's typical ObjectId format.
 *
 * Bean Validation annotations (e.g., @NotNull, @Size, @Email) from the original
 * entity are preserved and work seamlessly with Spring Boot validation.
 *
 * The {@code @Column(name = "phone_number")} annotation was translated to
 * {@code @Field("phone_number")} for MongoDB field mapping.
 *
 * The unique constraint on the email column defined in {@code @Table} has been translated
 * to {@code @Indexed(unique = true)} on the email field.
 *
 * {@code @XmlRootElement} annotation removed as JSON is the more common format for
 * Spring Boot REST APIs using Jackson/JSON-B by default.
 *
 * {@code @GeneratedValue} was removed as MongoDB typically handles ID generation,
 * especially when using String type for the ID field which defaults to ObjectId strings.
 *
 * SCHEMA RECOMMENDATIONS:
 * - Relationships: The original Member entity did not define relationships (@OneToMany, etc.).
 *   If relationships were added (e.g., to an Address entity):
 *     - Embedding: Consider embedding related data (like a list of Addresses) directly
 *       within the Member document if the related data is small, conceptually part of the
 *       Member, and frequently accessed together. This improves read performance (one query)
 *       but can lead to larger documents and potential data duplication if the embedded
 *       data is also used elsewhere.
 *     - Referencing: Use references (storing IDs of related documents, e.g., List<String> addressIds)
 *       if the related data is large, frequently modified independently, or accessed separately.
 *       This keeps documents smaller and avoids duplication but may require additional queries
 *       (lookups) to retrieve related data (e.g., using $lookup in aggregation or separate queries).
 *
 * - Indexing:
 *   - The 'email' field has a unique index (@Indexed(unique = true)) derived from the
 *     original @UniqueConstraint. This is crucial for performance of email lookups and
 *     enforcing uniqueness.
 *   - Consider adding {@code @Indexed} to 'phoneNumber' if lookups by phone number are frequent use cases.
 *     Example: {@code @Indexed} on the {@code phoneNumber} field.
 *   - Consider adding {@code @Indexed} to 'name' if sorting or frequent filtering by name is required.
 *     However, indexing names might be less effective if names are not highly selective or if
 *     case-insensitive/partial matching is needed (requiring text indexes or specific query patterns).
 *     Example: {@code @Indexed} on the {@code name} field.
 *   Indexes significantly speed up query filtering and sorting operations on the indexed fields
 *   but consume storage space and slightly slow down write operations (inserts, updates, deletes).
 *   Add indexes strategically based on actual query patterns and performance requirements.
 */
@SuppressWarnings("serial") // Original annotation kept
@Document(collection = "members") // Specifies the MongoDB collection name
public class Member implements Serializable { // Kept Serializable from original, review if necessary

    @Id // Marks this field as the primary identifier (_id) in MongoDB
    private String id; // Changed type to String for standard MongoDB ObjectId representation

    @NotNull
    @Size(min = 1, max = 25)
    @Pattern(regexp = "[^0-9]*", message = "Must not contain numbers")
    // Consider adding @Indexed if searching/sorting by name is common
    private String name;

    @NotNull
    @NotEmpty
    @Email
    @Indexed(unique = true) // Enforces uniqueness and speeds up lookups by email
    private String email;

    @NotNull
    @Size(min = 10, max = 12)
    @Digits(fraction = 0, integer = 12)
    @Field("phone_number") // Maps this field to 'phone_number' in the MongoDB document
    // Consider adding @Indexed here if searching by phone number is common
    private String phoneNumber;

    // Standard Getters and Setters

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhoneNumber() {
        return phoneNumber;
    }

    public void setPhoneNumber(String phoneNumber) {
        this.phoneNumber = phoneNumber;
    }
}
