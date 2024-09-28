const { SlashCommandBuilder } = require('discord.js');

module.exports = {
    data: new SlashCommandBuilder()
        .setName('ping')
        .setDescription('Replies with Pong!'),
    async execute(interaction) {
        // Respond with Pong and fetch the reply time
        const sent = await interaction.reply({ content: 'Pong!', fetchReply: true });

        // Calculate interaction latency
        const responseLatency = sent.createdTimestamp - interaction.createdTimestamp;

        // Get the bot's WebSocket ping
        const botLatency = interaction.client.ws.ping;

        // Edit the reply to include both latencies
        await interaction.editReply(`aaa! Response latency: ${responseLatency}ms. WebSocket ping: ${botLatency}ms.`);
    },
};
