/*
 * JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag. See the copyright.txt in the
 * distribution for a full listing of individual contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.migratedapp.component;

import jakarta.annotation.PostConstruct; // Spring also supports JSR-250 annotations like @PostConstruct
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;
import org.springframework.web.context.annotation.RequestScope;

import com.migratedapp.repository.MemberRepository;
import com.migratedapp.model.Member; // Assuming Member is translated to com.migratedapp.model.Member (@Document)
// Assuming a custom event class is created for Spring's event mechanism
// import com.migratedapp.event.MemberChangedEvent;

import java.util.List;

/**
 * Request-scoped component responsible for retrieving and holding the list of members
 * for the duration of a request.
 *
 * Original Java EE/CDI annotations like @Produces and @Named have been removed.
 * In Spring MVC, controllers should typically query this component/service and
 * add the necessary data (like the member list) to the Model.
 *
 * Event handling (@Observes) has been migrated to Spring's @EventListener.
 * Assumes a corresponding Spring ApplicationEvent (e.g., MemberChangedEvent)
 * will be published when a member changes.
 *
 * Depends on a Spring Data MongoDB MemberRepository.
 */
@Component
@RequestScope // Equivalent to CDI's @RequestScoped
public class MemberListProducer {

    private final MemberRepository memberRepository;

    private List<Member> members;

    /**
     * Constructs the MemberListProducer with the required MemberRepository dependency.
     * Uses Spring's constructor injection.
     *
     * @param memberRepository The repository for accessing member data.
     */
    @Autowired
    public MemberListProducer(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
    }

    /**
     * Provides the list of members retrieved from the repository.
     * Note: The original @Produces/@Named functionality (making this directly
     * available in EL like "members") is removed. Controllers should call this
     * method and add the result to the Spring Model.
     *
     * @return The current list of members for this request.
     */
    public List<Member> getMembers() {
        return members;
    }

    /**
     * Listens for an application event indicating a change in member data
     * and refreshes the member list for the current request.
     *
     * Replaces the CDI @Observes functionality.
     *
     * @param event The event indicating a member change. (Assuming a custom MemberChangedEvent exists)
     * TODO: Define and publish a suitable Spring ApplicationEvent (e.g., MemberChangedEvent containing the Member).
     *       The parameter type here might need adjustment based on the actual event class.
     */
    @EventListener
    // public void onMemberListChanged(MemberChangedEvent event) { // Example with custom event
    public void onMemberListChanged(Member member) { // Kept original param for structure, but review event strategy
        retrieveAllMembersOrderedByName();
    }

    /**
     * Initializes the component by retrieving all members ordered by name.
     * This method is called after the bean is constructed and dependencies are injected.
     * Uses Spring Data repository query derivation (findAllByOrderByNameAsc).
     *
     * Assumption: Member document has a 'name' field, and MemberRepository
     * has a method like 'findAllByOrderByNameAsc()'.
     */
    @PostConstruct
    public void retrieveAllMembersOrderedByName() {
        // Assuming the Spring Data repository method follows naming conventions
        // for sorting. e.g., findAllByOrderByNameAsc()
        members = memberRepository.findAllByOrderByNameAsc();
    }
}
