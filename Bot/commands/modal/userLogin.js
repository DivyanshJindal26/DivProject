const { Events } = require('discord.js');
const { getDb } = require('../../helpers/mongodb');
const fetch = require('node-fetch'); // Ensure you have this if not already

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isModalSubmit()) {
            if (interaction.customId === 'userLogin') {
                // Get the user's input from the modal
                const username = interaction.fields.getTextInputValue('login-username');
                const password = interaction.fields.getTextInputValue('login-password');

                try {
                    // Defer reply to avoid the 3-second timeout
                    await interaction.deferReply({ ephemeral: true });

                    const response = await fetch('http://127.0.0.1:5000/user/login', {
                        method: 'POST',
                        headers: {
                            'X-API-KEY': 'divyanshjindal',
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error('HTTP error ' + response.status);
                    }

                    const data = await response.json();
                    const userDB = getDb().collection('discord');
                    const token = data.token;
                    const userid = interaction.user.id;

                    await userDB.updateOne(
                        { userid: userid },
                        { $set: { tokens: token } },
                        { upsert: true }
                    );

                    // Edit the deferred reply with the success message
                    await interaction.editReply({
                        content: `Successfully logged into \`${username}\`.`,
                    });
                } catch (error) {
                    console.error('Error: ', error);
                    await interaction.editReply({
                        content: 'Failed to log in. Please try again.',
                    });
                }
            }
        }
    },
};
