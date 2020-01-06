Feature: Management of application by the manager

  Background:
    Given The manager is logged
    And Go to assistant home page

  Scenario: Edit administrative data of an assistant
    When Click on dashboard link
    Then Click randomly on edit assistant link
    Then Edit assistant administrative data

  Scenario: Substitute reviewer
    When Click on reviewers link
    Then Substitute reviewer

  Scenario: Delete reviewer
    When Click on reviewers link
    Then Delete reviewer

  Scenario: Add reviewer
    When Click on reviewers link
    Then Add reviewer

  Scenario: Reviewer should be unique
    When Click on reviewers link
    Then Add duplicate reviewer