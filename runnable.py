from langchain_core.runnables import RunnableLambda, RunnableParallel

add_one = RunnableLambda(lambda x: x + 1)

print(add_one.invoke(1))
print(add_one.batch([1, 2, 3]))

add_five = RunnableLambda(lambda x: x + 5)

add_six = add_one | add_five

print(add_six.invoke(1))

sequence = add_one | {"one": add_one, "five": add_five}

print(sequence.invoke(10))

add_parallel = RunnableParallel(
    {
        "one": add_one,
        "five": add_five,
    }
)

print(add_parallel.invoke(10))
