const { Events, EmbedBuilder } = require('discord.js');
const fetch = require('node-fetch'); // Ensure you have this if not already

module.exports = {
    name: Events.InteractionCreate,
    async execute(interaction) {
        if (interaction.isModalSubmit()) {
            if (interaction.customId === 'userCreate') {
                // Get the user's input from the modal
                const username = interaction.fields.getTextInputValue('create-username');
                const password = interaction.fields.getTextInputValue('create-password');
                const email = interaction.fields.getTextInputValue('create-email');


                    // Defer reply to avoid the 3-second timeout

                    const response = await fetch('http://127.0.0.1:5000/user/create', {
                        method: 'POST',
                        headers: {
                            'X-API-KEY': 'divyanshjindal',
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            username: username,
                            password: password,
                            email: email,
                        }),
                    });

                    if (!response.ok) {
                        console.log(response);
                        await interaction.reply('Error');
                    };

                    const data = await response.json();
                    
                    let embed = new EmbedBuilder()
                            .setColor(`#${Math.floor(Math.random() * 16777215).toString(16).padStart(6,'0')}`)
                            .setTitle('User Successfully Created')
                            .setDescription(`<:div_dot:1290739274966110240> Username: ${username}
                                <:div_dot:1290739274966110240> Password: ${password[0] + 'x'.repeat(password.length-2)+password[password.length-1]}
                                <:div_dot:1290739274966110240> Email ID: ${email}`);
                    // Edit the deferred reply with the success message
                    await interaction.reply(embed); 

            }
        }
    else {
    }
    },
};
