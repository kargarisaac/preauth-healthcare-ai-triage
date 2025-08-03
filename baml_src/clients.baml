// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

client<llm> GPT4_1_mini {
  provider openai
  options {
    model "gpt-4.1-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> GPT4oMini {
  provider openai
  options {
    model "gpt-4o-mini"
    api_key env.OPENAI_API_KEY
  }
}

client<llm> GPT4_1 {
  provider openai
  options {
    model "gpt-4.1"
    api_key env.OPENAI_API_KEY
  }
}
