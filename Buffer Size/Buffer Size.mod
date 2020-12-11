int num_agents = ...;
int num_capabilities = ...;

int crypto_size = ...;
int trust_model_size = ...;
int reputation_size = (num_agents-1) * num_capabilities * trust_model_size;
int stereotype_size = trust_model_size;

int total_memory_size_available = ...;
 
int num_buffers = ...;
range Buffers = 0..num_buffers-1;

int buffer_weights[i in Buffers] = ...;

dvar int+ buffer_sizes[Buffers];

dexpr int utility_crypto = minl(buffer_sizes[0], num_agents - 1);
dexpr int utility_trust = minl(buffer_sizes[1], num_capabilities * utility_crypto);
dexpr int utility_reputation = minl(buffer_sizes[2], utility_crypto);
dexpr int utility_stereotype = minl(buffer_sizes[3], num_capabilities * utility_crypto);

// Would make problem non-convex
//dexpr int reputation_size = buffer_sizes[0] * num_capabilities * trust_model_size;

dexpr int memory_used =
		crypto_size * buffer_sizes[0] +
		trust_model_size * buffer_sizes[1] +
		reputation_size * buffer_sizes[2] +
		stereotype_size * buffer_sizes[3];

//maximize sum(i in Buffers) buffer_weights[i] * buffer_sizes[i];
maximize buffer_weights[0] * utility_crypto +
		 buffer_weights[1] * utility_trust +
		 buffer_weights[2] * utility_reputation +
		 buffer_weights[3] * utility_stereotype;

subject to {
	ct01:
	memory_used <= total_memory_size_available;
	
	ct02:
	0 <= buffer_sizes[0] <= num_agents - 1;
	
	ct03:
	0 <= buffer_sizes[1] <= num_capabilities * (num_agents - 1);
	
	ct04:
	0 <= buffer_sizes[2] <= num_agents - 1;
	
	ct05:
	0 <= buffer_sizes[3] <= num_capabilities * (num_agents - 1);
}

execute {
	writeln("capacity = ", (
		buffer_sizes[0] / (num_agents - 1) +
		buffer_sizes[1] / (num_capabilities * (num_agents - 1)) +
		buffer_sizes[2] / (num_agents - 1) +
		buffer_sizes[3] / (num_capabilities * (num_agents - 1))
	) / 4);
}
