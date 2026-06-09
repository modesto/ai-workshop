---
name: awesome-assertions
description: |
  Skill for writing fluent and readable test assertions with AwesomeAssertions. Use this when you need clear assertions, object comparisons, collection validation, or complex matching scenarios. Covers the full API including Should(), BeEquivalentTo(), Contain(), ThrowAsync(), and more.
  Make sure to use this skill whenever the user mentions assertions, Should(), BeEquivalentTo, fluent assertions, AwesomeAssertions, or wants more readable test assertions, even if they don't explicitly ask for assertion guidance.
  Keywords: assertions, awesome assertions, fluent assertions, Should(), Be(), BeEquivalentTo, Contain, ThrowAsync, NotBeNull, object comparison, collection validation, exception assertions, AwesomeAssertions, FluentAssertions, fluent syntax
---

# AwesomeAssertions Fluent Assertion Guide

This skill provides a complete guide to writing high-quality test assertions with AwesomeAssertions, including core syntax, advanced techniques, and best practices.

## About AwesomeAssertions

**AwesomeAssertions** is the community fork of FluentAssertions, licensed under **Apache 2.0**, completely free, and unrestricted for commercial use.

### Core Features

- **Completely Free**: Apache 2.0 license, suitable for commercial projects
- **Fluent Syntax**: Natural-language style method chaining
- **Rich Assertions**: Covers objects, collections, strings, numbers, exceptions, and more
- **Excellent Error Messages**: Detailed and easy-to-understand failure output
- **High Performance**: Optimized implementation for efficient test execution
- **Extensible**: Supports custom assertion extension methods

### Relationship with FluentAssertions

AwesomeAssertions is a community fork of FluentAssertions. Key differences:

| Item | FluentAssertions | AwesomeAssertions |
| --- | --- | --- |
| **License** | Paid for commercial projects | Apache 2.0 (completely free) |
| **Namespace** | `FluentAssertions` | `AwesomeAssertions` |
| **API Compatibility** | Original | Highly compatible |
| **Community Support** | Official maintainers | Community maintainers |

---

## Installation and Setup

### Install via NuGet

```bash
# .NET CLI
dotnet add package AwesomeAssertions

# Package Manager Console
Install-Package AwesomeAssertions
```

### csproj Configuration (Recommended)

```xml
<ItemGroup>
  <PackageReference Include="AwesomeAssertions" Version="9.4.0" PrivateAssets="all" />
</ItemGroup>
```

### Namespace Imports

```csharp
using AwesomeAssertions;
using Xunit;
```

---

## Core Assertion Syntax

All assertions start with `.Should()` and continue with fluent method chaining.

| Category | Common Methods | Description |
| --- | --- | --- |
| **Objects** | `NotBeNull()`, `BeOfType<T>()`, `BeEquivalentTo()` | Null, type, and equality checks |
| **Strings** | `Contain()`, `StartWith()`, `MatchRegex()`, `BeEquivalentTo()` | Content, patterns, and case-insensitive comparison |
| **Numbers** | `BeGreaterThan()`, `BeInRange()`, `BeApproximately()` | Comparison, ranges, and floating-point precision |
| **Numeric Collections** | `EqualApproximately()`, `NotEqualApproximately()` | Approximate comparison for numeric collections (9.4+) |
| **Collections** | `HaveCount()`, `Contain()`, `BeEquivalentTo()`, `AllSatisfy()` | Count, content, order, and predicates |
| **Exceptions** | `Throw<T>()`, `NotThrow()`, `WithMessage()`, `WithInnerException()` | Exception type, message, and inner exception checks |
| **Async** | `ThrowAsync<T>()`, `CompleteWithinAsync()` | Async exception and completion validation |

> For complete syntax examples and code, see [references/core-assertions-syntax.md](references/core-assertions-syntax.md)

---

## Advanced Technique: Complex Object Comparison

Use `BeEquivalentTo()` with `options` for deep object comparison:

- **Exclude properties**: `options.Excluding(u => u.Id)` - exclude auto-generated fields
- **Dynamic exclusion**: `options.Excluding(ctx => ctx.Path.EndsWith("At"))` - pattern-based exclusion
- **Cyclic references**: `options.IgnoringCyclicReferences().WithMaxRecursionDepth(10)`

---

## Advanced Technique: Custom Assertion Extensions

Create domain-specific extension methods such as `product.Should().BeValidProduct()` and reusable exclusion helpers like `ExcludingAuditFields()`.

See [templates/custom-assertions-template.cs](templates/custom-assertions-template.cs) for the full implementation.

> For complete examples, see [references/complex-object-assertions.md](references/complex-object-assertions.md)

---

## Performance Optimization Strategies

- **Large datasets**: Use `HaveCount()` for a quick size check first, then validate samples (avoid full `BeEquivalentTo` on everything)
- **Selective comparison**: Use anonymous objects + `ExcludingMissingMembers()` to validate only critical properties

```csharp
// Selective property comparison - validate only critical fields
order.Should().BeEquivalentTo(new
{
    CustomerId = 123,
    TotalAmount = 999.99m,
    Status = "Pending"
}, options => options.ExcludingMissingMembers());
```

---

## New Features in Versions 9.2-9.4

### Approximate Comparison for Numeric Collections - `[Not]EqualApproximately` (9.4+)

For `INumber<T>` numeric collections, new approximate equality assertions are available (.NET 8+ required):

```csharp
// Verify numeric collections are approximately equal within tolerance
var actual = new[] { 1.001f, 2.002f, 3.003f };
actual.Should().EqualApproximately(new[] { 1f, 2f, 3f }, 0.01f);

// Verify collections are not approximately equal within tolerance
actual.Should().NotEqualApproximately(new[] { 10f, 20f, 30f }, 0.01f);
```

> **Difference from `BeApproximately()`**: `BeApproximately()` is for a single numeric value, while `EqualApproximately()` is for numeric collections and compares elements one by one. When tolerance is 0, `EqualApproximately` behaves the same as `Equal`.

### Max Item Count for Collection Formatting (9.4+)

When an assertion fails, collections show the first 32 items by default. You can now customize this via `FormattingOptions`:

```csharp
// Set collection display limit within AssertionScope
using var scope = new AssertionScope();
scope.FormattingOptions.MaxItems = 100; // Default is 32

largeCollection.Should().BeEquivalentTo(expected);
```

You can also override it with a custom formatter:

```csharp
class LargeCollectionFormatter : EnumerableValueFormatter
{
    protected override int MaxItems => 100;
    public override bool CanHandle(object value) => value is IEnumerable<MyEntity>;
}
```

### Occurrence Constraints in Collections (9.2+)

The `Contain` method now supports occurrence constraints:

```csharp
var numbers = new[] { 1, 2, 2, 3, 3, 3 };
numbers.Should().Contain(2, AtLeast.Once());
numbers.Should().Contain(3, Exactly.Times(3));
```

### Null-Safety Improvement - `[return: NotNull]` (9.4+)

All `Should()` and assertion methods now include `[return: NotNull]` so nullable analysis can track null state correctly:

```csharp
// Before 9.4: still considered potentially null after Should(), requiring !
var user = GetUser();
user.Should().NotBeNull();
user!.Name.Should().Be("test"); // ! needed to suppress warning

// After 9.4: Should().NotBeNull() returns with [NotNull], compiler infers non-null
user.Should().NotBeNull();
user.Name.Should().Be("test"); // ! no longer needed
```

### Excluding Members by Name (9.3+)

`BeEquivalentTo` supports excluding members by name:

```csharp
actual.Should().BeEquivalentTo(expected, options => options
    .Excluding(ctx => ctx.Name == "InternalState"));
```

---

## Best Practices and Team Standards

### Test Naming Convention

Follow the `Method_Scenario_ExpectedResult` pattern (for example, `CreateUser_ValidEmail_ShouldReturnActiveUser`).

### Better Failure Messages

Add a `because` string to provide clear failure context:

```csharp
result.IsSuccess.Should().BeFalse("because negative payment amounts are not allowed");
```

### Using AssertionScope

Use `AssertionScope` to collect multiple failures and show all issues at once:

```csharp
using (new AssertionScope())
{
    user.Should().NotBeNull("User creation should not fail");
    user.Id.Should().BeGreaterThan(0, "User should have a valid ID");
    user.Email.Should().NotBeNullOrEmpty("Email is required");
}
```

---

## Common Scenarios and Solutions

| Scenario | Key Technique |
| --- | --- |
| API response validation | `BeEquivalentTo()` + `Including()` for selective comparison |
| Database entity validation | `BeEquivalentTo()` + `Excluding()` for auto-generated fields |
| Event validation | Capture subscribed events and validate each property |

> For full code examples, see [references/common-scenarios.md](references/common-scenarios.md)

---

## Troubleshooting

### Problem 1: BeEquivalentTo fails, but objects look identical

**Cause**: Objects may include auto-generated fields or timestamps.

**Solution**:

```csharp
// Exclude dynamic fields
actual.Should().BeEquivalentTo(expected, options => options
    .Excluding(x => x.Id)
    .Excluding(x => x.CreatedAt)
    .Excluding(x => x.UpdatedAt)
);
```

### Problem 2: Collection order mismatch causes failure

**Cause**: Different collection order.

**Solution**:

```csharp
// Use BeEquivalentTo to ignore order
actual.Should().BeEquivalentTo(expected); // does not check order

// Or explicitly require order
actual.Should().Equal(expected); // checks order
```

### Problem 3: Floating-point comparison fails

**Cause**: Floating-point precision issues.

**Solution**:

```csharp
// Single numeric value with precision tolerance
actualValue.Should().BeApproximately(expectedValue, 0.001);

// Numeric collections with EqualApproximately (9.4+, .NET 8+ required)
actualValues.Should().EqualApproximately(expectedValues, 0.001);
```

---

## When to Use This Skill

### Applicable Scenarios

When writing unit tests or integration tests.
When validating complex object structures.
When comparing API responses or database entities.
When you need clear failure messages.
When establishing domain-specific testing standards.

### Not Applicable Scenarios

Performance testing (use dedicated benchmarking tools).
Load testing (use K6, JMeter, etc.).
UI testing (use Playwright, Selenium).

---

## Combining with Other Skills

### With unit-test-fundamentals

Use `unit-test-fundamentals` to build test structure first, then use this skill for assertions:

```csharp
[Fact]
public void Calculator_Add_TwoPositiveNumbers_ShouldReturnSum()
{
    // Arrange - follow the AAA pattern
    var calculator = new Calculator();

    // Act
    var result = calculator.Add(2, 3);

    // Assert - use AwesomeAssertions
    result.Should().Be(5);
}
```

### With test-naming-conventions

Use naming rules from `test-naming-conventions` together with assertions from this skill:

```csharp
[Fact]
public void CreateUser_ValidData_ShouldReturnActiveUser()
{
    var user = userService.CreateUser("test@example.com");

    user.Should().NotBeNull()
        .And.BeOfType<User>();
    user.IsActive.Should().BeTrue();
}
```

### With xunit-project-setup

Install and use AwesomeAssertions in projects created with `xunit-project-setup`.

---

## Output Format

- Generate test assertions using AwesomeAssertions fluent syntax
- Use Should().Be/BeEquivalentTo/Contain style method chains
- Include examples for object comparison, collection validation, and exception assertions
- Provide `.csproj` package reference (AwesomeAssertions)

## Reference Resources

### Source Articles

This skill content is distilled from the "Old-School Software Engineer Testing Practice - 30-Day Challenge" series:

- **Day 04 - AwesomeAssertions Fundamentals and Practical Techniques**
  - Article: https://ithelp.ithome.com.tw/articles/10374188
  - Sample code: https://github.com/kevintsengtw/30Days_in_Testing_Samples/tree/main/day04

- **Day 05 - AwesomeAssertions Advanced Techniques and Complex Scenarios**
  - Article: https://ithelp.ithome.com.tw/articles/10374425
  - Sample code: https://github.com/kevintsengtw/30Days_in_Testing_Samples/tree/main/day05

### Official Resources

- **AwesomeAssertions GitHub**: https://github.com/AwesomeAssertions/AwesomeAssertions
- **AwesomeAssertions Official Docs**: https://awesomeassertions.org/

### Related Article

- **Fluent Assertions License Change Discussion**: https://www.dotblogs.com.tw/mrkt/2025/04/19/152408

---

## Summary

AwesomeAssertions provides powerful and readable assertion syntax and is an important tool for building high-quality tests. Through:

1. **Fluent syntax**: makes test code easier to read
2. **Rich assertions**: covers many data types (9.4 adds approximate numeric collection comparison)
3. **Custom extensions**: enables domain-specific assertions
4. **Performance optimization**: handles large data scenarios (9.4 adds collection display limit customization)
5. **Completely free**: Apache 2.0 license with no commercial restriction
6. **Null safety**: `[return: NotNull]` in 9.4 improves nullable analysis

Remember: good assertions do more than verify results. They clearly communicate expected behavior and provide useful diagnostic information when failures occur.

See [templates/assertion-examples.cs](templates/assertion-examples.cs) for more practical examples.
