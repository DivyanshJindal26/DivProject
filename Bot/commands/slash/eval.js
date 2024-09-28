const { SlashCommandBuilder } = require('discord.js');
const { OWNER_ID } = require('../../config')
module.exports = {
    data: new SlashCommandBuilder()
        .setName('eval')
        .setDescription('Evaluate a JavaScript expression')
        .addStringOption(option => 
            option.setName('expression')
                .setDescription('The expression to evaluate')
                .setRequired(true)),
    async execute(interaction) {
        // Check if the user is the owner
        if (interaction.user.id !== OWNER_ID) {
            return interaction.reply({ content: 'You are not authorized to use this command.', ephemeral: true });
        }

        const expression = interaction.options.getString('expression');

        try {
            const result = eval(expression);
            await interaction.reply(`Result: ${result}`);
        } catch (error) {
            await interaction.reply(`Error: ${error.message}`);
        }
    },
};
