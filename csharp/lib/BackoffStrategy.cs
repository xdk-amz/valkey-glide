// Copyright Valkey GLIDE Project Contributors - SPDX Identifier: Apache-2.0

namespace Glide;

/// <summary>
/// Represents the strategy used to determine how and when to reconnect, in case of connection failures.
/// The time between attempts grows exponentially, to the formula rand(0 .. factor * (exponentBase ^ N)),
/// where N is the number of failed attempts.
/// </summary>
public class BackoffStrategy
{
    public int NumOfRetries { get; }
    public int Factor { get; }
    public int ExponentBase { get; }
    public int? JitterPercent { get; }

    public BackoffStrategy(int numOfRetries, int factor, int exponentBase, int? jitterPercent = null)
    {
        NumOfRetries = numOfRetries;
        Factor = factor;
        ExponentBase = exponentBase;
        JitterPercent = jitterPercent;
    }
}
