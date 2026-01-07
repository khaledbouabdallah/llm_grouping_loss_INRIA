# Data Selection Criteria

## Entities Selection (Notebook 01)

Selected entities must meet ALL criteria:

1. **Entity Type**: Person
2. **Wikipedia Texts**: Available in English, French, Arabic with non-empty summaries
3. **Required Facts**: Must have birthPlace, nationality, birthDate
4. **Complete Fact Labels**: Birth place AND nationality must have labels in English, French, AND Arabic

## Why These Filters

- **Wikipedia in 3 languages**: Required for generating text embeddings in all target languages
- **Complete facts**: Required for generating 3 types of multiple-choice questions
- **Birth place AND nationality labels in all languages**: Required for distractor generation - without Arabic labels, cannot generate Arabic questions for these fact types

## Results

- **Initial entities with Wikipedia**: ~26,000+
- **After fact label filtering**: ~23,000+ (removes entities with missing Arabic/French labels for birthPlace or nationality)
- **Final selection**: Entities with 100% data coverage in all three languages

This ensures question generation succeeds for all entity/language combinations without missing label failures.
